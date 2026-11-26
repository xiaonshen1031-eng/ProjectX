"""Render the Chinese workflow film with Windows Speech, Pillow and FFmpeg."""

from datetime import timedelta
import json
from pathlib import Path
import subprocess
import wave

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'docs/assets'
WORKFLOW = (
    ('task', '调度任务', '何时还有充电容量？',
     '一台容量上限为五十五千瓦的变压器为五辆车供电。车辆只能在各自的接入窗口内充电。算例要确定每小时该分配多少功率。',
     ('55 kW', '变压器容量上限', '5 辆', '各有充电窗口')),
    ('data', '数据入模', '基础负荷占用多少容量？',
     '用变压器上限减去当小时的基础负荷，就得到可分配给充电的功率。十时的基础负荷为二十五千瓦，因此最多可分配三十千瓦。',
     ('55 − 25 kW', '上限减基础负荷', '30 kW', '10:00 可分配功率')),
    ('model', '模型约束', '从逐车功率算回负荷',
     '每辆车只在接入窗口内分配功率。各车功率之和加上基础负荷，得到变压器负荷。再对每辆车的功率积分，核对它获得的电量。',
     ('25 + 30 kW', '基础负荷加分配功率', '55 kW', '10:00 变压器负荷')),
    ('compute', '独立复算', '把分配量代回上限',
     '十时共分配三十千瓦，变压器负荷达到五十五千瓦。一辆车如需增加充电功率，就得查看它在哪些有余量的时段仍可接入。',
     ('55 = 55 kW', '实际负荷达到上限', '0 kW', '10:00 容量余量')),
    ('visual', '结果解释', '总容量能否供足所需电量？',
     '需求放大为基准的四倍时，五辆车共需四百千瓦时。可分配功率在八个时段累计最多只能供二百五十七千瓦时。即使放宽到八个时段全部接入，仍差一百四十三千瓦时。',
     ('400 − 257 kWh', '需求减可供电量上界', '143 kWh', '电量缺口')),
    ('charts', '图件复核', '在一条时间轴上查看调度',
     '将充电功率和接入窗口画在同一时间轴上，就能核对分配发生在哪些时段。这里使用工程图册中的独立合成示例。', 'gantt'),
    ('delivery', '报告交付', '把依据放在判断旁边',
     '报告在负荷图旁解释容量用满的时段。需求超过可供电量的情况放在情景比较处，读者可以用相同参数复算。',
     ('容量用满', '逐时负荷对照容量上限', '电量不足', '情景需求对照可供电量')),
)
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


def font(size, bold=False):
    filename = 'msyhbd.ttc' if bold else 'msyh.ttc'
    return ImageFont.truetype(str(Path('C:/Windows/Fonts') / filename), size)


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
    if isinstance(panel, tuple):
        for x, offset in ((450, 0), (832, 2)):
            draw.rounded_rectangle((x, 366, x + 351, 601), radius=12, fill='#eaf0ff', outline='#bfcde7')
            write((x + 22, 407), panel[offset + 1], 22, '#435371')
            write((x + 22, 461), panel[offset], 36, '#2452dc', True)
        draw.line((802, 481, 828, 481), fill='#2452dc', width=3)
        draw.polygon(((828, 481), (820, 476), (820, 486)), fill='#2452dc')
    else:
        with Image.open(ROOT / f'docs/downloads/figures/python/zh/{panel}.png') as source:
            plot = source.convert('RGB')
        plot.thumbnail((765, 343), Image.Resampling.LANCZOS)
        image.paste(plot, (419 + (807 - plot.width) // 2, 302 + (363 - plot.height) // 2))
    return image


def timestamp(seconds):
    whole = str(timedelta(seconds=round(seconds, 3)))
    return whole.zfill(8) + '.000' if '.' not in whole else whole[:-3].zfill(12)


def render(key, scenes, heading, poster):
    work = ROOT / 'work/film-122' / key
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
        chapter_id, label, _, narration, _ = scene
        frame(scene, heading).save(work / f'{index}.png')
        with wave.open(str(work / f'{index}.wav')) as audio:
            duration = audio.getnframes() / audio.getframerate()
        target = work / f'{index}.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', '24',
                        '-i', f'{index}.png', '-i', f'{index}.wav', '-shortest', '-r', '24',
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
    frame(scenes[0], heading).save(ASSETS / poster, quality=94)
    (ASSETS / f'{key}-demo.zh.vtt').write_text('\n'.join(captions), encoding='utf-8')
    print(f'{key} demo: {len(chapters)} scenes, {start:.2f} seconds')
    return round(start, 3), chapters


def main():
    length, chapters = render('workflow', WORKFLOW, '充电调度 · 合成算例', 'project-workflow-poster.webp')
    render('charts', ATLAS, '工程图册 · 合成示例', 'charts-film-poster.webp')
    release = ROOT / 'docs/release.json'
    manifest = json.loads(release.read_text(encoding='utf-8'))
    manifest['video'].update(duration=length, chapters=chapters,
                             content='Synthetic charging allocation and report workflow')
    release.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
