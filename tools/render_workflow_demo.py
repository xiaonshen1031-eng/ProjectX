"""Replay the ProjectX demo commands and render their outputs with Chinese narration."""

import argparse
import csv
from datetime import timedelta
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
from tempfile import mkdtemp
from textwrap import wrap
import wave

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'docs/assets'
SKILL = ROOT / 'skill/senior-projectx'
ATLAS = (
    ('time', '容量约束', '何时最接近上限？',
     '在同一时轴上对照均值和第九十百分位数。下图给出它们到上限的距离，可以找到高位曲线最接近上限的时刻。', 'trajectory'),
    ('distribution', '条件分布', '样本集中在哪个区间？',
     '每行对应一个工况。沿同一刻度读取各行的密度峰和四分位区间，可以分辨整体位移与分布变宽。', 'ridges'),
    ('flow', '流量守恒', '同一总量如何分配？',
     '流带宽度表示分配量。三列的节点总量相同，沿流带可以查到不同输入最终分到了哪个输出。', 'sankey'),
    ('space', '节点采样', '哪些节点位于强场区域？',
     '用空间坐标定位各节点。右侧按场强重新排序，对照编号即可回到节点在网络中的位置。', 'spatial'),
    ('feasibility', '可行域', '哪条边界制约状态调整？',
     '箭头指向距离原状态最近的可行点。右侧给出移动距离，可用约束符号查看该点落在哪条边界上。', 'feasibility'),
    ('paired', '配对比较', '哪些差值区间跨过零？',
     '每行汇总同一工况下的三十六个配对差。左图呈现差值分布，右侧用零线对照均值区间。', 'forest'),
)


def csv_preview(path, fields, limit):
    with path.open(encoding='utf-8-sig', newline='') as source:
        rows = list(csv.DictReader(source))[:limit]
    widths = [max([len(field), *(len(row[field]) for row in rows)]) for field in fields]
    header = '  '.join(field.ljust(width) for field, width in zip(fields, widths))
    body = ['  '.join(row[field].ljust(width) for field, width in zip(fields, widths)) for row in rows]
    return [header, *body]


def capture_workflow(work):
    """Use the same CLI as the walkthrough and record what the run actually emits."""
    guide = (SKILL / 'references/project-allocation-demo.md').read_text(encoding='utf-8')
    blocks = re.findall(r'```powershell\n(.*?)```', guide, flags=re.S)
    scripts = {'scripts/project_demo.py', 'scripts/project_research.py', 'scripts/project_report.py'}
    runs = {}
    for block in blocks:
        for command in block.splitlines():
            if not command.strip():
                continue
            launcher, script, action, *args = shlex.split(command)
            if launcher != 'python' or script not in scripts:
                raise ValueError(f'Unexpected walkthrough command: {command}')
            kind = Path(args[0]).stem if action == 'audit-data' else action
            output = subprocess.check_output([sys.executable, '-X', 'utf8', str(SKILL / script), action, *args],
                                             cwd=work, encoding='utf-8')
            runs[kind] = (command, json.loads(output))
            print(f'Ran {action} ({kind})', flush=True)
    (work / 'run-log.json').write_text(json.dumps(runs, indent=2, ensure_ascii=False), encoding='utf-8')
    demo = work / 'demo'
    for kind in ('periods', 'vehicles', 'validate-allocation'):
        if runs[kind][1]['status'] != 'pass':
            raise ValueError(f'{kind} did not pass in the filmed replay')
    if runs['solve-allocation'][1]['status'] != 'optimal':
        raise ValueError('The filmed run did not produce an optimal allocation')
    figures = {item['id']: Path(item['path']) for item in runs['figures'][1]['artifacts']}
    validation = runs['validate-allocation'][1]

    def select(kind, *keys, files=()):
        command, result = runs[kind]
        fields = [f'{key}: {result[key]}' for key in keys]
        return command, [*fields, *(str(file) for file in files)]

    def relative(path):
        return path.relative_to(work).as_posix()

    return (
        ('data', '准备数据', '生成时段负荷与车辆输入表',
         '先生成两张合成数据表。时段表列出基础负荷、容量和时长，车辆表记录每辆车的接入窗口及充电需求。',
         ([select('prepare', 'status', files=('demo/data/periods.csv', 'demo/data/vehicles.csv'))],
          ['periods.csv', *csv_preview(demo / 'data/periods.csv',
                                      ('period', 'timestamp', 'base_load_kw', 'capacity_kw', 'duration_h'), 4)])),
        ('check', '检查输入', '核对时段和车辆字段',
         '把输入表和字段定义交给检查命令。两份结果各自记录行数和检查状态。',
         ([select('periods', 'status', 'rows'), select('vehicles', 'status', 'rows')],
          ['vehicles.csv', *csv_preview(demo / 'data/vehicles.csv',
                                        ('vehicle_id', 'arrival_period', 'departure_period', 'energy_kwh', 'max_charge_kw'), 3)])),
        ('solve', '求解与复算', '计算逐车充电功率',
         '用输入表和模型参数求解。分配表逐行记录每辆车在各时段得到的充电功率。',
         ([select('solve-allocation', 'status', files=('demo/data/results/allocation.csv',))],
          ['allocation.csv', *csv_preview(demo / 'data/results/allocation.csv',
                                         ('vehicle_id', 'period', 'charge_kw'), 4)])),
        ('validate', '复算分配', '用分配表回算电量和余量',
         '把分配功率按时长折算，再对每辆车求和，核对离站电量。将各车功率和基础负荷相加，复算变压器的容量余量。',
         ([select('validate-allocation', 'status', 'maximum_energy_residual_kwh', 'minimum_capacity_margin_kw',
                  files=('demo/review/validation.json',))], [])),
        ('sweep', '比较工况', '改变需求倍率，重算分配',
         '改变车辆需求电量后重新求解。结果表记录各需求倍率的求解状态，以及这些时段的容量余量。',
         ([select('sensitivity', 'status', 'scenarios', files=('demo/data/results/sensitivity.csv',))],
          ['sensitivity.csv', *csv_preview(demo / 'data/results/sensitivity.csv',
                                          ('demand_scale', 'status', 'minimum_margin_kw', 'mean_margin_kw'), 4)])),
        ('plot', '执行绘图', '从实际结果表导出三张图',
         '绘图命令读取刚才生成的分配和工况结果。同一批输出包括负荷诊断图、车辆接入图和工况比较图。',
         ([select('figures', files=(*map(relative, figures.values()), 'demo/review/figure_manifest.json'))], [])),
        ('read', '查看生成图', '找出容量最紧的时段',
         '打开生成的负荷诊断图。上方叠放总负荷和容量上限，下方画出两者的差。'
         f"时段 {validation['tightest_period']} 的容量余量最小，为 {validation['minimum_capacity_margin_kw']:g} 千瓦。",
         figures['figure_process']),
        ('windows', '查看生成图', '逐车查看接入窗口和分配',
         '切到同一次生成的接入图。每行对应一辆车，格内数字是该时段的充电功率，右侧对照实际交付和需求电量。',
         figures['figure_balance']),
    )


def font(size, bold=False):
    filename = 'msyhbd.ttc' if bold else 'msyh.ttc'
    return ImageFont.truetype(str(Path('C:/Windows/Fonts') / filename), size)


def workflow_frame(scene, heading, show_outputs=True):
    _, label, title, _, panel = scene
    image = Image.new('RGB', (1280, 720), '#ebf2fd')
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1280, 66), fill='#103286')
    draw.text((52, 14), 'ProjectX', font=font(27, True), fill='white')
    draw.text((1228, 24), heading, anchor='ra', font=font(17), fill='#e1edff')
    draw.text((52, 88), label, font=font(19, True), fill='#2451ca')
    draw.text((52, 123), title, font=font(40, True), fill='#142048')
    if isinstance(panel, Path):
        with Image.open(panel) as source:
            plot = source.convert('RGB')
        plot.thumbnail((1176, 372), Image.Resampling.LANCZOS)
        draw.rounded_rectangle((52, 176, 1228, 552), radius=13, fill='white', outline='#afc5ec', width=2)
        image.paste(plot, ((1280 - plot.width) // 2, 176 + (376 - plot.height) // 2))
        return image

    transcripts, preview = panel
    mono = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 21)
    draw.rounded_rectangle((52, 189, 1228, 654), radius=13, fill='#101e43')
    draw.text((79, 208), '运行命令与输出', font=font(17), fill='#a4bfed')
    draw.line((78, 241, 1200, 241), fill='#435780')
    y = 260
    for command, output in transcripts:
        for row in wrap(f'> {command}', width=94, subsequent_indent='  ', break_on_hyphens=False):
            draw.text((79, y), row, font=mono, fill='#eef4ff')
            y += 23
        if show_outputs:
            for row in output:
                draw.text((79, y), row, font=mono, fill='#a8d7ff')
                y += 23
        y += 8
    if preview and show_outputs:
        draw.line((78, y, 1200, y), fill='#435780')
        y += 12
        for row in preview:
            draw.text((79, y), row, font=mono, fill='#d9e6ff')
            y += 23
    if y > 650:
        raise ValueError(f'Terminal output overflows scene {scene[0]}')
    return image


def frame(scene, heading):
    _, label, title, narration, panel = scene
    image = Image.new('RGB', (1280, 720), '#f2f5fc')
    draw = ImageDraw.Draw(image)

    def write(position, text, size, color='#131419', bold=False):
        draw.text(position, text, font=font(size, bold), fill=color)

    draw.rectangle((0, 0, 1280, 102), fill='#172b65')
    write((52, 28), 'ProjectX', 32, 'white', True)
    write((1222 - font(18).getlength(heading), 38), heading, 18, '#e0e9ff')
    write((52, 145), label, 20, '#2452dc', True)
    write((52, 188), title, 44, bold=True)
    draw.line((56, 275, 1224, 275), fill='#bfcde7', width=2)
    body_width, body_size = 323, 23
    body_font = font(body_size)
    line, row = '', 0
    for char in narration:
        if body_font.getlength(line + char) > body_width:
            write((56, 320 + row * 38), line, body_size, '#435371')
            row, line = row + 1, ''
        line += char
    write((56, 320 + row * 38), line, body_size, '#435371')
    draw.rounded_rectangle((419, 302, 1226, 665), radius=14, fill='white', outline='#bfcde7', width=2)
    with Image.open(ROOT / f'docs/downloads/figures/python/zh/{panel}.png') as source:
        plot = source.convert('RGB')
    plot.thumbnail((765, 343), Image.Resampling.LANCZOS)
    image.paste(plot, (419 + (807 - plot.width) // 2, 302 + (363 - plot.height) // 2))
    return image


def timestamp(seconds):
    whole = str(timedelta(seconds=round(seconds, 3)))
    return whole.zfill(8) + '.000' if '.' not in whole else whole[:-3].zfill(12)


def render(key, scenes, heading, poster, work):
    work.mkdir(parents=True, exist_ok=True)
    speech = [
        "Add-Type -AssemblyName System.Speech",
        "$speaker=New-Object System.Speech.Synthesis.SpeechSynthesizer",
        "$voice=$speaker.GetInstalledVoices() | Where-Object {$_.Enabled -and "
        "$_.VoiceInfo.Culture.Name -eq 'zh-CN'} | Select-Object -First 1",
        "if (!$voice) {throw 'Chinese Windows Speech voice required'}",
        "$speaker.SelectVoice($voice.VoiceInfo.Name)",
        "$speaker.Rate=3",
    ]
    for index, (_, _, _, narration, _) in enumerate(scenes):
        speech.extend([f"$speaker.SetOutputToWaveFile('{index}.wav')",
                       f"$speaker.Speak('{narration}')", "$speaker.SetOutputToNull()"])
    (work / 'speak.ps1').write_text('\n'.join(speech), encoding='utf-8-sig')
    subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                    '-File', 'speak.ps1'], cwd=work, check=True)
    playlist, captions, chapters = [], ['WEBVTT', ''], []
    start = 0
    for index, scene in enumerate(scenes):
        chapter_id, label, _, narration, panel = scene
        with wave.open(str(work / f'{index}.wav')) as audio:
            duration = audio.getnframes() / audio.getframerate()
        if key == 'workflow' and not isinstance(panel, Path):
            workflow_frame(scene, heading, show_outputs=False).save(work / f'{index}-command.png')
            workflow_frame(scene, heading).save(work / f'{index}.png')
            reveal = min(3, duration * .3)
            timeline = (f"file '{index}-command.png'\nduration {reveal:.3f}\n"
                        f"file '{index}.png'\nduration {duration - reveal + .1:.3f}\nfile '{index}.png'\n")
            input_list = work / f'{index}-frames.txt'
            input_list.write_text(timeline, encoding='utf-8')
            video_input = ['-f', 'concat', '-safe', '1', '-i', input_list.name]
        else:
            make_frame = workflow_frame if key == 'workflow' else frame
            make_frame(scene, heading).save(work / f'{index}.png')
            video_input = ['-loop', '1', '-framerate', '24', '-i', f'{index}.png']
        target = work / f'{index}.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', *video_input, '-i', f'{index}.wav', '-shortest', '-r', '24',
                        '-c:v', 'libx264', '-crf', '21', '-preset', 'veryfast', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '96k', '-ar', '48000', target.name], cwd=work, check=True)
        actual = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                                              'format=duration', '-of', 'csv=p=0', str(target)]).strip())
        playlist.append(f"file '{target.name}'")
        chapters.append(dict(id=chapter_id, title=label, start=round(start, 3),
                             duration=round(actual, 3), text=narration))
        phrases = [segment + '。' for segment in narration.rstrip('。').split('。')]
        cursor = start
        cue_duration = min(duration, actual)
        for phrase in phrases:
            end = cursor + cue_duration * len(phrase) / len(narration)
            captions.extend([f'{timestamp(cursor)} --> {timestamp(end)}', phrase, ''])
            cursor = end
        start += actual
    (work / 'playlist.txt').write_text('\n'.join(playlist) + '\n', encoding='utf-8')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '1', '-i',
                    'playlist.txt', '-c', 'copy', '-movflags', '+faststart',
                    str(ASSETS / f'ProjectX-{key}-demo.mp4')], cwd=work, check=True)
    with Image.open(work / '0.png') as image:
        image.save(ASSETS / poster, quality=94)
    (ASSETS / f'{key}-demo.zh.vtt').write_text('\n'.join(captions), encoding='utf-8')
    print(f'{key} demo: {len(chapters)} scenes, {start:.2f} seconds')
    return round(start, 3), chapters


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workflow-only', action='store_true', help='Keep the separate atlas film unchanged.')
    args = parser.parse_args()
    (ROOT / 'work').mkdir(exist_ok=True)
    work = Path(mkdtemp(prefix='workflow-film-', dir=ROOT / 'work'))
    scenes = capture_workflow(work)
    length, chapters = render('workflow', scenes, '充电调度 · 合成数据', 'project-workflow-poster.webp', work)
    if not args.workflow_only:
        render('charts', ATLAS, '工程图册 · 合成示例', 'charts-film-poster.webp', work / 'atlas')
    release = ROOT / 'docs/release.json'
    manifest = json.loads(release.read_text(encoding='utf-8'))
    manifest['video'].update(duration=length, chapters=chapters,
                             content='Synthetic charging allocation, captured CLI outputs, and generated figures')
    release.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
