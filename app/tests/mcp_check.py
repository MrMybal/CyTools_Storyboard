"""Real MCP call: the official MCP client starts `tool.py mcp` over stdio, like an AI client.

It builds a project on a 3D stage (stage, shapes, a panel framed with two cameras, a
per-panel placement), renders it, reads the camera move, and writes
data/reports/mcp-check.json. Projects go to a temporary folder. Run from anywhere:

    runtime\\python\\Scripts\\python.exe app\\tests\\mcp_check.py
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent


def payload(result):
    return json.loads(result.content[0].text)


async def run_job(session, operation, parameters):
    job = payload(await session.call_tool('op_' + operation, {'parameters': parameters}))
    for _ in range(300):
        if job['state'] in ('Completed', 'Failed', 'Cancelled'):
            break
        await asyncio.sleep(0.2)
        job = payload(await session.call_tool('cy_get_job', {'jobId': job['jobId']}))
    if job['state'] != 'Completed':
        raise RuntimeError(f'{operation}: {job.get("error")}')
    return job['outputs']


async def main():
    temp = Path(tempfile.mkdtemp(prefix='story-mcp-'))
    env = {**os.environ, 'CYTOOLS_STORYBOARD_PROJECTS': str(temp / 'projects')}
    server = StdioServerParameters(command=sys.executable, env=env,
                                   args=[str(APP / 'tool.py'), '--data-dir', str(temp / 'jobs'), 'mcp'], cwd=str(Path.home()))
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = [t.name for t in (await session.list_tools()).tools]
            project = (await run_job(session, 'create_storyboard', {'title': 'MCP stage'}))['project']
            doc = (await run_job(session, 'add_panel', {'project': project, 'title': 'Arrival', 'duration': 5}))['document']
            panel = doc['sequences'][0]['panels'][0]['id']
            stage = (await run_job(session, 'add_stage', {'project': project, 'name': 'Street'}))['document']['stages'][0]['id']
            await run_job(session, 'add_object', {'project': project, 'stage': stage, 'shape': 'box', 'name': 'Wall',
                                                  'position': [0, 1.5, -3], 'scale': [8, 3, 0.4]})
            doc = (await run_job(session, 'add_object', {'project': project, 'stage': stage, 'shape': 'mannequin',
                                                         'name': 'Tom'}))['document']
            tom = doc['stages'][0]['objects'][1]['id']
            await run_job(session, 'set_panel_layout', {
                'project': project, 'panel': panel, 'mode': '3d', 'stage': stage,
                'camera': {'position': [0, 1.6, 7], 'target': [0, 1.2, 0], 'fov': 40},
                'cameraEnd': {'position': [4, 1.6, 5], 'target': [0, 1.2, 0], 'fov': 40}})
            custom = (await run_job(session, 'add_pose', {'project': project, 'name': 'Tom waves', 'angles': {
                'r_arm': [10, 140, 60], 'head': [20, 0]}}))['document']['poses'][0]['id']
            await run_job(session, 'update_pose', {'project': project, 'pose': custom, 'angles': {'twist': 10}})
            await run_job(session, 'override_object', {'project': project, 'panel': panel, 'object': tom,
                                                       'position': [1, 0, 1], 'rotation': [0, -30, 0],
                                                       'positionEnd': [-1, 0, 2], 'pose': 'standing',
                                                       'poseEnd': custom})
            rendered = await run_job(session, 'render_panel_layout', {'project': project, 'panel': panel})
            move = await run_job(session, 'suggest_camera_move', {'project': project, 'panel': panel, 'apply': True})
            await run_job(session, 'add_panel', {'project': project, 'title': 'Second', 'duration': 4,
                                                 'prompt': {'action': 'Tom walks to the wall.'}})
            film = await run_job(session, 'export_h3_film', {'project': project, 'options': {'overlapFrames': 22}})
            converted = await run_job(session, 'export_h3_workflow', {'project': project, 'options': {
                'chain': 'always', 'controlSource': 'pose'}})
    report = {'tools': len(tools), 'layoutTools': sorted(t for t in tools if t.endswith(('stage', 'object', 'layout', 'move'))),
              'render': rendered, 'move': move}
    report['film'] = {'folder': film['folder'], 'segments': [(s['startFrame'], s['endFrame'], s['overlap'])
                                                             for s in film['segments']], 'warnings': film['warnings']}
    steps = json.loads(Path(converted['file']).read_text(encoding='utf-8'))['steps']
    report['workflow'] = {'file': converted['file'], 'generations': converted['generations'],
                          'steps': [s['id'] for s in steps]}
    report['ok'] = (Path(rendered['render']).is_file() and Path(rendered['depth']).is_file()
                    and move['cameraMove'] == 'arc shot' and (Path(film['folder']) / 'film.json').is_file()
                    and report['film']['segments'][1][2] == 22 and Path(converted['file']).is_file()
                    and report['workflow']['steps'][-1] == 'film'
                    and steps[0]['params']['control']['video'].startswith('media/pose_'))
    out = ROOT / 'data' / 'reports' / 'mcp-check.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=1))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
