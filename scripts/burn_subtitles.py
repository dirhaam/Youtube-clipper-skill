#!/usr/bin/env python3
"""
烧录字幕到视频
处理 FFmpeg libass 支持和路径空格问题
"""

import sys
import os
import shutil
import subprocess
import tempfile
import platform
from pathlib import Path
from typing import Dict, Optional

from utils import format_file_size


def detect_ffmpeg_variant() -> Dict:
    """
    检测 FFmpeg 版本和 libass 支持

    Returns:
        Dict: {
            'type': 'full' | 'standard' | 'none',
            'path': FFmpeg 可执行文件路径,
            'has_libass': 是否支持 libass
        }
    """
    print("🔍 检测 FFmpeg 环境...")

    # 优先检查 ffmpeg-full（macOS）
    if platform.system() == 'Darwin':
        # Apple Silicon
        full_path_arm = '/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg'
        # Intel
        full_path_intel = '/usr/local/opt/ffmpeg-full/bin/ffmpeg'

        for full_path in [full_path_arm, full_path_intel]:
            if Path(full_path).exists():
                has_libass = check_libass_support(full_path)
                print(f"   找到 ffmpeg-full: {full_path}")
                print(f"   libass 支持: {'✅ 是' if has_libass else '❌ 否'}")
                return {
                    'type': 'full',
                    'path': full_path,
                    'has_libass': has_libass
                }

    # 检查标准 FFmpeg
    standard_path = shutil.which('ffmpeg')
    if standard_path:
        has_libass = check_libass_support(standard_path)
        variant_type = 'full' if has_libass else 'standard'
        print(f"   找到 FFmpeg: {standard_path}")
        print(f"   类型: {variant_type}")
        print(f"   libass 支持: {'✅ 是' if has_libass else '❌ 否'}")
        return {
            'type': variant_type,
            'path': standard_path,
            'has_libass': has_libass
        }

    # 未找到 FFmpeg
    print("   ❌ 未找到 FFmpeg")
    return {
        'type': 'none',
        'path': None,
        'has_libass': False
    }


def check_libass_support(ffmpeg_path: str) -> bool:
    """
    检查 FFmpeg 是否支持 libass（字幕烧录必需）

    Args:
        ffmpeg_path: FFmpeg 可执行文件路径

    Returns:
        bool: 是否支持 libass
    """
    try:
        # 检查是否有 subtitles 滤镜
        result = subprocess.run(
            [ffmpeg_path, '-filters'],
            capture_output=True,
            text=True,
            timeout=5
        )

        # 查找 subtitles 滤镜
        return 'subtitles' in result.stdout.lower()

    except Exception:
        return False


def install_ffmpeg_full_guide():
    """
    显示安装 ffmpeg-full 的指南
    """
    print("\n" + "="*60)
    print("⚠️  需要安装 ffmpeg-full 才能烧录字幕")
    print("="*60)

    if platform.system() == 'Darwin':
        print("\nmacOS 安装方法:")
        print("  brew install ffmpeg-full")
        print("\n安装后，FFmpeg 路径:")
        print("  /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg  (Apple Silicon)")
        print("  /usr/local/opt/ffmpeg-full/bin/ffmpeg     (Intel)")
    else:
        print("\n其他系统:")
        print("  请从源码编译 FFmpeg，确保包含 libass 支持")
        print("  参考: https://trac.ffmpeg.org/wiki/CompilationGuide")

    print("\n验证安装:")
    print("  ffmpeg -filters 2>&1 | grep subtitles")
    print("="*60)


def burn_subtitles(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    ffmpeg_path: str = None,
    font_size: int = 24,
    margin_v: int = 30,
    watermark_text: str = None
) -> str:
    """
    烧录字幕到视频（使用临时目录解决路径空格问题）

    Args:
        video_path: 输入视频路径
        subtitle_path: 字幕文件路径（SRT 格式）
        output_path: 输出视频路径
        ffmpeg_path: FFmpeg 可执行文件路径（可选）
        font_size: 字体大小，默认 24
        margin_v: 底部边距，默认 30
        watermark_text: 水水印文本（可选）

    Returns:
        str: 输出视频路径
    """
    video_path = Path(video_path)
    subtitle_path = Path(subtitle_path)
    output_path = Path(output_path)

    # 验证输入文件
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    burn_subs = True
    if str(subtitle_path).lower() == 'none':
        burn_subs = False
    elif not subtitle_path.exists():
        raise FileNotFoundError(f"Subtitle file not found: {subtitle_path}")

    # 检测 FFmpeg (仅当需要烧录字幕时才强制检查 libass，如果只是 watermark 可能不需要 full libass? 
    # 其实 drawtext 也通常包含在标准 build 中，但为了安全起见保持检查，或者如果不需要字幕跳过 libass 检查)
    if ffmpeg_path is None:
        ffmpeg_info = detect_ffmpeg_variant()
        
        # 如果不烧录字幕，其实不需要 libass，但为了简单起见，且通常用户已安装，我们暂不放宽检查
        # 除非确认 standard ffmpeg 有 drawtext 但没 libass
        
        if ffmpeg_info['type'] == 'none':
            install_ffmpeg_full_guide()
            raise RuntimeError("FFmpeg not found")

        # Only enforce libass if we are actually burning subtitles
        if burn_subs and not ffmpeg_info['has_libass']:
            install_ffmpeg_full_guide()
            raise RuntimeError("FFmpeg does not support libass (subtitles filter)")

        ffmpeg_path = ffmpeg_info['path']

    print(f"\n🎬 处理视频 (字幕: {'✅' if burn_subs else '❌'}, 水印: {'✅' if watermark_text else '❌'})...")
    print(f"   视频: {video_path.name}")
    if burn_subs:
        print(f"   字幕: {subtitle_path.name}")
    print(f"   输出: {output_path.name}")
    if watermark_text:
        print(f"   Watermark: {watermark_text}")
    print(f"   FFmpeg: {ffmpeg_path}")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix='youtube_clipper_')
    print(f"   使用临时目录: {temp_dir}")

    try:
        # 复制文件到临时目录
        temp_video = os.path.join(temp_dir, 'video.mp4')
        temp_output = os.path.join(temp_dir, 'output.mp4')
        
        shutil.copy(video_path, temp_video)
        
        if burn_subs:
            temp_subtitle = os.path.join(temp_dir, 'subtitle.srt')
            shutil.copy(subtitle_path, temp_subtitle)

        # 构建 FFmpeg 命令
        filters = []
        
        if burn_subs:
            filters.append(f"subtitles=subtitle.srt:force_style='FontSize={font_size},MarginV={margin_v}'")
        
        # Add Watermark if provided
        if watermark_text:
            # Escape text for ffmpeg
            safe_text = watermark_text.replace(":", "\\:").replace("'", "'")
            
            # Platform-specific font path
            font_file = ""
            if platform.system() == 'Windows':
                font_path = "C:/Windows/Fonts/arial.ttf"
                if os.path.exists(font_path):
                    font_file = f":fontfile='{font_path.replace(':', '\\:')}'"
            elif platform.system() == 'Darwin':
                font_path = "/System/Library/Fonts/Helvetica.ttc"
                if os.path.exists(font_path):
                    font_file = f":fontfile='{font_path}'"
            
            watermark_filter = f"drawtext=text='{safe_text}'{font_file}:x=(w-text_w)/2:y=(h-text_h)/2:fontsize=50:fontcolor=white@0.3:shadowcolor=black@0.5:shadowx=3:shadowy=3"
            filters.append(watermark_filter)

        if not filters:
            # No filters, just copy? Or error?
            # If user script called this, they likely expect processing. 
            # If no subs and no watermark, just copy input to output?
            print("   ⚠️ 无需处理 (无字幕且无水印)，直接复制...")
            shutil.copy(video_path, output_path)
            return str(output_path)

        filter_complex = ",".join(filters)

        # 注意：这里使用相对路径，稍后会在 cwd=temp_dir 下运行
        cmd = [
            ffmpeg_path,
            '-i', 'video.mp4',       # 输入文件（相对路径）
            '-vf', filter_complex,
            '-c:a', 'copy',          # 音频直接复制
            '-y',                    # 覆盖输出
            'output.mp4'             # 输出文件（相对路径）
        ]


        print(f"   执行 FFmpeg...")
        print(f"   命令: {' '.join(cmd)}")

        # 执行 FFmpeg
        #关键修复：在临时目录下运行，避免路径问题
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=temp_dir  # 在临时目录下执行
        )

        if result.returncode != 0:
            print(f"\n❌ FFmpeg 执行失败:")
            print(result.stderr)
            raise RuntimeError(f"FFmpeg failed with return code {result.returncode}")

        # 验证输出文件
        if not Path(temp_output).exists():
            raise RuntimeError("Output file not created")

        # 移动输出文件到目标位置
        print(f"   移动输出文件...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(temp_output, output_path)

        # 获取文件大小
        output_size = output_path.stat().st_size
        print(f"✅ 字幕烧录完成")
        print(f"   输出文件: {output_path}")
        print(f"   文件大小: {format_file_size(output_size)}")

        return str(output_path)

    finally:
        # 清理临时目录
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"   清理临时目录")
        except Exception:
            pass


def main():
    """命令行入口"""
    if len(sys.argv) < 4:
        print("Usage: python burn_subtitles.py <video> <subtitle> <output> [font_size] [margin_v]")
        print("\nArguments:")
        print("  video      - 输入视频文件路径")
        print("  subtitle   - 字幕文件路径（SRT 格式）")
        print("  output     - 输出视频文件路径")
        print("  font_size  - 字体大小，默认 24")
        print("  margin_v   - 底部边距，默认 30")
        print("\nExample:")
        print("  python burn_subtitles.py input.mp4 subtitle.srt output.mp4")
        print("  python burn_subtitles.py input.mp4 subtitle.srt output.mp4 28 40")
        sys.exit(1)

    video_path = sys.argv[1]
    subtitle_path = sys.argv[2]
    output_path = sys.argv[3]
    font_size = int(sys.argv[4]) if len(sys.argv) > 4 else 24
    margin_v = int(sys.argv[5]) if len(sys.argv) > 5 else 30
    watermark_text = sys.argv[6] if len(sys.argv) > 6 else None

    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv()
    ffmpeg_path = os.getenv('FFMPEG_PATH')

    try:
        result_path = burn_subtitles(
            video_path,
            subtitle_path,
            output_path,
            ffmpeg_path=ffmpeg_path,
            font_size=font_size,
            margin_v=margin_v,
            watermark_text=watermark_text
        )

        print(f"\n✨ 完成！输出文件: {result_path}")

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
