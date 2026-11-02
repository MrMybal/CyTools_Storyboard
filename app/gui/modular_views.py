# Host document adapters for the unchanged, pinned CyUI modules.
from copy import deepcopy
from hashlib import blake2b
import json, math, time
import cyui
from imgui_bundle import imgui
from cyui_modules.common import Range
from cyui_modules.timeline import Clip, Lane, Marker, TimelineState, timeline
from cyui_modules.inspector import InspectorState, Property, inspector
from ui_common import tr
from storyboard import model

def stable(value):
    return int.from_bytes(blake2b(str(value).encode('utf-8'),digest_size=8).digest(),'big') or 1

def transaction(editor, action):
    before=json.dumps(editor.board.doc,sort_keys=True)
    try:
        action()
        after=json.dumps(editor.board.doc,sort_keys=True)
    except Exception:
        editor.board.restore(json.loads(before))
        raise
    if after==before:return False
    editor.undo.append(before);editor.undo=editor.undo[-200:];editor.redo.clear()
    editor.last_state=after;editor.last_change=time.monotonic();editor.dirty=True
    return True

class TimelineView:
    def __init__(self):
        self.state=TimelineState();self.signature=None;self.revision=0
        self.document=None;self.mode=0;self.active=0;self.zoom=None;self.last_frame=-1

    def prepare(self,editor):
        board=editor.board;key=str(board.folder)
        signature=json.dumps(board.doc,sort_keys=True)
        if key!=self.document:
            self.state=TimelineState();self.signature=None;self.zoom=None;self.document=key
        if signature!=self.signature:
            self.signature=signature;self.revision+=1
        panels={stable(p['id']):p for p in board.panels()}
        rows=board.timeline();clips=[];ends=[]
        for n,row in enumerate(rows):
            # Separate overlapping crossfades so both panels keep reachable trim handles.
            track=next((k for k,end in enumerate(ends) if end<=row['start']+1e-8),len(ends))
            if track==len(ends):ends.append(row['end'])
            else:ends[track]=row['end']
            clips.append(Clip(stable(row['id']),stable('storyboard-track:'+str(track)),
                              float(row['start']),float(row['end']-row['start']),
                              f"{n+1}. {panels[stable(row['id'])]['title']}",n))
        lanes=[Lane(stable('storyboard-track:'+str(k)),tr('Storyboard') if k==0 else tr('Transitions'),46)
               for k in range(max(1,len(ends)))]
        return lanes,clips,panels

    def apply(self,editor,edit,panels):
        # Every preview belongs to CyUI until a validated release commits one Undo step.
        if edit.phase=='begin':self.mode=self.state.mode;self.active=self.state.active
        if edit.phase!='commit':return False
        changed={c.id:c for c in edit.value}
        active=panels.get(self.active);shown=changed.get(self.active)
        if active is None or shown is None:return False
        if not all(math.isfinite(c.start) and math.isfinite(c.duration) and .1-1e-8<=c.duration<=600+1e-8 for c in edit.value):
            editor.message=tr('Timeline duration must be between 0.1 and 600 seconds.')
            return False
        if self.mode in (2,3):
            duration=round(shown.duration,2)
            return transaction(editor,lambda:active.update(duration=duration))
        if self.mode==1:
            # Ordered panels are gapless: moving a clip reorders it within its sequence.
            sequence,_,_=editor.board.find(active['id'])
            targets=[p for p in sequence['panels'] if p['id']!=active['id']]
            starts={c.id:c.start for c in self.state.before}
            position=sum(shown.start>starts.get(stable(p['id']),0)+p['duration']/2 for p in targets)
            return transaction(editor,lambda:editor.board.move_panel(active['id'],sequence['id'],position))
        return False

    def draw(self,editor):
        lanes,clips,panels=self.prepare(editor)
        cyui.overline(tr('TIMELINE'));imgui.same_line()
        imgui.set_next_item_width(cyui.dp(150))
        zoomed,editor.px_per_second=cyui.slider_bar('##tlzoom',editor.px_per_second,5.,200.,'%.0f px/s')
        cyui.tooltip(tr('Timeline zoom'));imgui.same_line()
        cyui.text_faint(tr('Drag the right edge of a panel to change its duration.'))
        width=max(1,imgui.get_content_region_avail().x-min(cyui.dp(150),imgui.get_content_region_avail().x*.3))
        if self.zoom is None or zoomed:
            start=max(0,self.state.view.minimum)
            self.state.view=Range(start,start+width/max(1,editor.px_per_second))
        self.zoom=editor.px_per_second
        if not self.state.mode:self.state.selected=[stable(editor.selected)] if editor.selected else []
        frame=imgui.get_frame_count()
        if self.last_frame>=0 and frame-self.last_frame>1:self.state.mode=0
        self.last_frame=frame
        def overlay(clip,rect):
            panel=panels[clip.id];a,b=rect;p=cyui.palette()
            from .common import colour
            fill=imgui.get_color_u32(colour(panel['color'])) if panel.get('color') else p.bg4
            fill=cyui.mix(fill,p.accent,.35) if clip.id in self.state.selected else fill
            d=imgui.get_window_draw_list();d.add_rect_filled(a,b,fill,cyui.dp(3))
            d.add_rect(a,b,p.accent if clip.id in self.state.selected else p.line,cyui.dp(3))
            ink=cyui.contrast_text(fill)
            cyui.clipped_text(d,(a[0]+cyui.dp(5),a[1]+cyui.dp(3)),b[0]-a[0]-cyui.dp(10),ink,clip.label)
            cyui.clipped_text(d,(a[0]+cyui.dp(5),a[1]+cyui.dp(23)),b[0]-a[0]-cyui.dp(10),cyui.alpha(ink,.7),f'{clip.duration:.1f}s')
        result=timeline('##storyboard-timeline',self.state,lanes,clips,
                        size=(0,max(cyui.dp(62),imgui.get_content_region_avail().y)),
                        playhead=editor.play_time() if editor.play else 0.,revision=self.revision,
                        draw_clip=overlay,min_duration=.1)
        editor.px_per_second=width/max(1e-9,self.state.view.span)
        if self.state.selected and self.state.selected[-1] in panels:
            editor.selected=panels[self.state.selected[-1]]['id']
        self.apply(editor,result['clips'],panels)
        if result['seek'] is not None:
            point=max(0,min(editor.board.total_duration(),result['seek']))
            editor.play={'start':time.monotonic()-point,'paused_at':point}
        if result['remove']:
            ids=[panels[key]['id'] for key in result['remove'] if key in panels]
            if ids:
                transaction(editor,lambda:[editor.board.remove_panel(key) for key in ids])
                if editor.selected in ids:editor.selected=None

class PanelInspector:
    def __init__(self):
        self.state=InspectorState();self.key=None;self.signature=None;self.revision=0
    def draw(self,editor,panel):
        key=(str(editor.board.folder),panel['id'])
        signature=json.dumps(editor.board.doc,sort_keys=True)
        if key!=self.key:self.state=InspectorState();self.key=key;self.signature=None
        if self.signature!=signature:self.revision+=1;self.signature=signature
        keys={stable(panel['id']+':'+key):key for key in ('title','duration','status')}
        fields=[Property(stable(panel['id']+':title'),'Title',panel['title']),
                Property(stable(panel['id']+':duration'),'Duration',float(panel['duration']),
                         help='Seconds on screen; the presets set it at once.',minimum=.1,maximum=600.),
                Property(stable(panel['id']+':status'),'Status',panel['status'],choices=model.STATUSES)]
        for key,edit in inspector('##panel-properties',self.state,fields,revision=self.revision):
            if edit.phase=='commit':
                field=keys[key];value=round(float(edit.value),2) if field=='duration' else edit.value
                transaction(editor,lambda:panel.update({field:value}))
