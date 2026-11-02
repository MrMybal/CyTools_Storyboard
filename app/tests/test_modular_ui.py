import hashlib,json,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
from dataclasses import replace
from imgui_bundle import imgui as i
import cyui
APP=Path(__file__).resolve().parents[1]

class Provenance(unittest.TestCase):
    def test_exact_and_selective_sources(self):
        pin=json.loads((APP/'cyui-source.json').read_text('utf-8'))
        self.assertFalse(pin['modifications'])
        self.assertEqual(len(pin['revision']),40)
        for rel,digest in pin['files'].items():
            actual=(APP/rel).read_text('utf-8').replace('\r\n','\n').encode('utf-8')
            self.assertEqual(hashlib.sha256(actual).hexdigest(),digest,rel)
        self.assertEqual({p.name for p in (APP/'cyui_modules').glob('*.py')},
                         {Path(p).name for p in pin['files'] if p.startswith('cyui_modules/')})
        self.assertEqual((APP/'LICENCES/CyUI-MIT.txt').read_text('utf-8'),
                         (APP.parent/'LICENCES/CyUI-MIT.txt').read_text('utf-8'))

    def test_log_append_preserves_selection_and_source_change_resets_it(self):
        from gui_log_view import LogView
        view=LogView();view.update('INFO First\n','one')
        _,before=view.buffer.snapshot();view.state.selected=before[0].id
        view.update('INFO First\nERROR Second\n','one')
        _,after=view.buffer.snapshot()
        self.assertEqual(view.state.selected,after[0].id)
        self.assertEqual(after[0].id,before[0].id)
        view.update('WARNING Other\n','two')
        _,after=view.buffer.snapshot();self.assertEqual(len(after),1)
        self.assertEqual(after[0].source,'two');self.assertEqual(view.state.selected,0)

class FrameCase(unittest.TestCase):
    def setUp(self):
        i.create_context();io=i.get_io();io.display_size=(1100,850);io.delta_time=1/60
        io.set_ini_filename('');io.backend_flags|=i.BackendFlags_.renderer_has_textures
        io.config_input_trickle_event_queue=False;io.mouse_double_click_time=.001
        cyui.apply()
    def tearDown(self):i.destroy_context()
    def frame(self,draw,position=(-100,-100),button=None,key=None):
        io=i.get_io();io.add_mouse_pos_event(*position)
        if button is not None:io.add_mouse_button_event(*button)
        if key is not None:io.add_key_event(*key)
        i.new_frame();i.set_next_window_pos((0,0));i.set_next_window_size((1100,850))
        i.begin('Adapter',None,i.WindowFlags_.no_title_bar|i.WindowFlags_.no_move|i.WindowFlags_.no_saved_settings)
        i.set_cursor_screen_pos((20,20))
        try:result=draw()
        finally:i.end();i.render()
        return result

class StoryboardFrames(FrameCase):
    def setUp(self):
        super().setUp();self.temp=tempfile.TemporaryDirectory()
        from storyboard.model import Storyboard
        from gui.main import Editor
        board=Storyboard.create(Path(self.temp.name),'Fixture')
        a=board.add_panel(title='First');b=board.add_panel(title='Second')
        a['transition']={'type':'crossfade','duration':1.}
        self.editor=Editor.__new__(Editor);e=self.editor
        e.board=board;e.selected=a['id'];e.undo=[];e.redo=[]
        e.last_state=json.dumps(board.doc,sort_keys=True);e.last_change=0.;e.dirty=False
        e.px_per_second=40.;e.play=None;e.message=''
    def tearDown(self):
        self.temp.cleanup();super().tearDown()

    def test_timeline_preserves_crossfades_and_commits_one_undo(self):
        from gui.modular_views import TimelineView
        from cyui_modules.common import Edit
        e=self.editor;view=TimelineView();_,clips,panels=view.prepare(e)
        self.assertEqual(clips[1].start,4.)
        view.state.active=clips[0].id;view.state.mode=3;view.state.before=deepcopy(clips)
        before=deepcopy(e.board.doc)
        view.apply(e,Edit('begin',clips),panels)
        proposed=[replace(c,duration=7.) if c.id==clips[0].id else c for c in clips]
        view.apply(e,Edit('update',proposed),panels)
        self.assertEqual(e.board.doc,before);self.assertFalse(e.undo)
        self.assertTrue(view.apply(e,Edit('commit',proposed),panels))
        self.assertEqual(len(e.undo),1);self.assertEqual(e.board.panels()[0]['duration'],7.)
        e.undo_step();self.assertEqual(e.board.doc,before)
        e.redo_step();self.assertEqual(e.board.panels()[0]['duration'],7.)
        _,clips,panels=view.prepare(e);view.active=clips[0].id;view.mode=3
        bad=[replace(c,duration=float('nan')) if c.id==clips[0].id else c for c in clips]
        self.assertFalse(view.apply(e,Edit('commit',bad),panels))
        self.assertEqual(e.board.panels()[0]['duration'],7.)

    def test_native_trim_escape_revision_and_single_commit(self):
        from gui.modular_views import TimelineView
        e=self.editor;view=TimelineView();rect=[]
        def draw():
            view.draw(e);rect[:]=[tuple(i.get_item_rect_min()),tuple(i.get_item_rect_max())]
        self.frame(draw);self.frame(draw)
        a,b=rect;left=a[0]+min(cyui.dp(150),(b[0]-a[0])*.3)
        scale=(b[0]-left)/view.state.view.span
        x=left+5*scale-2;y=a[1]+i.get_frame_height()+10
        self.frame(draw,(x,y),(0,True))
        self.assertEqual(view.state.mode,3)
        self.frame(draw,(x+60,y))
        self.assertEqual(e.board.panels()[0]['duration'],5.)
        self.frame(draw,(x+60,y),key=(i.Key.escape,True))
        self.assertEqual(e.board.panels()[0]['duration'],5.);self.assertFalse(e.undo)
        self.frame(draw,(x+60,y),(0,False),key=(i.Key.escape,False))
        self.frame(draw,(x,y),(0,True));self.frame(draw,(x+40,y))
        e.board.doc['title']='External revision'
        self.frame(draw,(x+40,y));self.assertEqual(view.state.mode,0);self.assertFalse(e.undo)
        self.frame(draw,(x+40,y),(0,False))
        self.frame(draw,(x,y),(0,True));self.frame(draw,(x+40,y));self.frame(draw,(x+40,y),(0,False))
        self.assertEqual(len(e.undo),1);self.assertGreater(e.board.panels()[0]['duration'],5.)

    def test_shared_views_all_themes_and_dpi(self):
        from gui.modular_views import TimelineView,PanelInspector
        from cyui_modules.locale import set_locale
        e=self.editor;view=TimelineView();properties=PanelInspector()
        for theme,*_ in cyui.THEMES:
            for density in ('compact','comfortable'):
                for dpi in (1.,1.5,2.):
                    cyui.apply(theme,density,dpi)
                    for language in ('en','fr'):
                        set_locale(language)
                        self.frame(lambda:view.draw(e))
                        self.frame(lambda:properties.draw(e,e.board.panels()[0]))
        set_locale('en')

    def test_host_transaction_rolls_back_atomically(self):
        from gui.modular_views import transaction
        e=self.editor;before=deepcopy(e.board.doc)
        def fail():
            e.board.panels()[0]['duration']=10.
            raise ValueError('Rejected edit')
        with self.assertRaises(ValueError):transaction(e,fail)
        self.assertEqual(e.board.doc,before);self.assertFalse(e.undo)


    def test_direct_script_entrypoint_uses_package_independent_adapters(self):
        import runpy
        namespace=runpy.run_path(str(APP/'gui/main.py'),run_name='storyboard_entrypoint')
        self.frame(lambda:namespace['Editor'].timeline(self.editor))
