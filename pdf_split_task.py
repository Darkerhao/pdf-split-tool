from typing import List, Tuple, Dict, Any
from PyPDF2 import PdfReader, PdfWriter
import os
import re

from task_context import TaskContext, TaskCancelledError
from services.pdf_service import normalize_page_ranges


def validate_chapters_per_unit(chapters_per_unit: int) -> int:
    if chapters_per_unit <= 0:
        raise ValueError("每个单元的章节数必须大于 0")
    return chapters_per_unit


def split_pdf_by_ranges(
    ctx: TaskContext,
    input_path: str,
    output_path: str,
    ranges: List[Tuple[int, int]],
):
    """
    PDF 拆分任务（按页码范围）

    :param ctx: TaskContext
    :param input_path: 输入 PDF
    :param output_path: 输出 PDF
    :param ranges: [(start_page, end_page)]，页码从 1 开始（包含）
    """

    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)

        normalized_ranges = normalize_page_ranges(ranges, total_pages)

        if not normalized_ranges:
            raise ValueError("没有有效的页码范围可导出")

        # 计算总工作量（用于进度）
        total_units = sum(end - start + 1 for start, end in normalized_ranges)
        completed_units = 0

        ctx.report_progress(0, "开始拆分 PDF")

        base_dir = os.path.dirname(output_path) or os.getcwd()
        base_name, ext = os.path.splitext(os.path.basename(output_path))
        if not ext:
            ext = ".pdf"

        exported_paths: List[str] = []

        for start, end in normalized_ranges:
            ctx.check_cancelled()

            writer = PdfWriter()

            for page_index in range(start - 1, end):
                ctx.check_cancelled()

                writer.add_page(reader.pages[page_index])

                completed_units += 1
                progress = completed_units / total_units * 100

                ctx.report_progress(
                    progress,
                    f"处理中：第 {page_index + 1} 页 / 共 {total_pages}  页"
                )

            if len(normalized_ranges) == 1:
                current_output_path = output_path
            else:
                current_output_path = os.path.join(
                    base_dir,
                    f"{base_name}_{start}-{end}{ext}",
                )

            with open(current_output_path, "wb") as f:
                writer.write(f)

            exported_paths.append(current_output_path)

        ctx.report_progress(100, "拆分完成")
        if len(exported_paths) == 1:
            ctx.report_done("PDF 拆分完成", exported_paths[0])
        else:
            ctx.report_done(f"已导出 {len(exported_paths)} 个 PDF 文件", exported_paths)

    except TaskCancelledError:
        ctx.report_done("操作已取消", None)

    except Exception as e:
        ctx.report_error(str(e))


def extract_text_from_pdf(pdf_path: str) -> Dict[int, str]:
    """
    从PDF文件中提取文本，按页码组织

    :param pdf_path: PDF文件路径
    :return: 字典，键为页码（从1开始），值为该页的文本内容
    """
    reader = PdfReader(pdf_path)
    text_by_page = {}
    
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text = page.extract_text() or ""
        text_by_page[page_num + 1] = text
    
    return text_by_page


# def detect_chapters(text_by_page: Dict[int, str]) -> List[Tuple[int, int]]:
#     """
#     智能识别PDF文档中的章节结构

#     :param text_by_page: 按页码组织的文本内容
#     :return: 章节范围列表，每个元素为(章节起始页, 章节结束页)
#     """
#     chapters = []
#     current_chapter_start = None
#     chapter_patterns = [
#         r'^\s*第\s*([一-九零壹贰叁肆伍陆柒捌玖拾]+|[0-9]+)\s*卷\s*',  # 卷格式：第1卷、第一卷
#         r'^\s*第\s*([一-九零壹贰叁肆伍陆柒捌玖拾]+|[0-9]+)\s*章\s*',  # 中文章节格式：第1章、第一章
#         r'^\s*Chapter\s*([0-9]+)\s*',  # 英文章节格式：Chapter 1
#         r'^\s*CHAPTER\s*([0-9]+)\s*',  # 英文大写章节格式：CHAPTER 1
#         r'^\s*Section\s*([0-9]+(\.[0-9]+)?)\s*',  # 节格式：Section 1.1
#         r'^\s*SECTION\s*([0-9]+(\.[0-9]+)?)\s*',  # 大写节格式：SECTION 1.1
#         r'^\s*\d+\s*\.\s*',  # 数字编号格式：1. 引言
#     ]
    
#     # 额外的卷格式检查
#     volume_patterns = [
#         r'^\s*卷\s*([一-九零壹贰叁肆伍陆柒捌玖拾]+|[0-9]+)\s*',  # 卷格式：卷一、卷1
#         r'^\s*Volume\s*([0-9]+)\s*',  # 英文卷格式：Volume 1
#         r'^\s*VOLUME\s*([0-9]+)\s*',  # 英文大写卷格式：VOLUME 1
#     ]
    
#     # 遍历所有页面，寻找章节标题
#     for page_num in sorted(text_by_page.keys()):
#         text = text_by_page[page_num]
#         lines = text.split('\n')
        
#         for line in lines:
#             line = line.strip()
#             if not line:
#                 continue
            
#             # 检查是否匹配章节标题模式
#             is_chapter_title = False
#             for pattern in chapter_patterns:
#                 if re.match(pattern, line):
#                     is_chapter_title = True
#                     break
            
#             # 检查是否匹配卷格式
#             if not is_chapter_title:
#                 for pattern in volume_patterns:
#                     if re.match(pattern, line):
#                         is_chapter_title = True
#                         break
            
#             # 检查是否可能是章节标题（基于字体大小推断，通过文本特征判断）
#             if not is_chapter_title:
#                 # 基于文本特征的启发式判断
#                 if (len(line) < 50 and  # 标题通常较短
#                     line.isupper() and  # 全大写可能是标题
#                     len(line.split()) < 10):  # 单词数较少
#                     is_chapter_title = True
#                 elif (len(line) < 30 and  # 标题通常较短
#                       line.endswith('章') or line.endswith('节') or line.endswith('卷') or 
#                       line.endswith('章：') or line.endswith('节：') or line.endswith('卷：')):  # 中文标题特征，添加卷
#                     is_chapter_title = True
            
#             if is_chapter_title:
#                 # 如果已经在处理一个章节，先结束当前章节
#                 if current_chapter_start is not None:
#                     chapters.append((current_chapter_start, page_num - 1))
#                 # 开始新章节
#                 current_chapter_start = page_num
#                 break
    
#     # 处理最后一章
#     if current_chapter_start is not None:
#         last_page = max(text_by_page.keys())
#         chapters.append((current_chapter_start, last_page))
    
#     # 验证和清理章节范围
#     validated_chapters = []
#     for start, end in chapters:
#         if start <= end:
#             validated_chapters.append((start, end))
    
#     return validated_chapters

CN_NUM = "零一二三四五六七八九十百千〇○壹贰叁肆伍陆柒捌玖拾佰仟"

# ========= 标题正则库（覆盖三大类文档） =========
CHAPTER_REGEXES = [
    # 小说 / 中文书籍
    rf'^第\s*([{CN_NUM}0-9]+)\s*[章回卷部篇](?:\s|$)',
    rf'^卷\s*([{CN_NUM}0-9]+)(?:\s|$)',

    # 英文章节
    r'^(chapter|CHAPTER)\s+([0-9IVXLC]+)\b',

    # 教材常见结构
    r'^([0-9]+)\.\s+\S+',            # 1. Title
    r'^([0-9]+\.[0-9]+)\s+\S+',      # 1.1 Title
    r'^section\s+([0-9.]+)\b',
    r'^SECTION\s+([0-9.]+)\b',

    # 论文结构
    r'^([IVXLC]+)\.\s+\S+',          # I. INTRODUCTION
    r'^([0-9]+)\s+[A-Z][A-Z\s]+$',   # 1 INTRODUCTION（全大写）
]

TOC_KEYWORDS = ["目录", "contents", "CONTENTS"]

def is_probable_toc_page(text: str) -> bool:
    """判断是否为目录页"""
    lines = text.lower().split("\n")[:20]
    score = 0
    for line in lines:
        if any(k in line for k in TOC_KEYWORDS):
            score += 2
        if re.search(r'\.{3,}\s*\d+$', line):  # ...... 23
            score += 1
    return score >= 3


def normalize_chapter_id(raw: str) -> int:
    """把中文数字转成整数（用于递增校验）"""
    cn_map = {
        '零':0,'〇':0,'○':0,
        '一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,
        '十':10,'百':100,'千':1000,
        '壹':1,'贰':2,'叁':3,'肆':4,'伍':5,'陆':6,'柒':7,'捌':8,'玖':9,
        '拾':10,'佰':100,'仟':1000
    }

    if raw.isdigit():
        return int(raw)

    total = 0
    unit = 1
    num = 0
    for char in reversed(raw):
        if char in cn_map:
            val = cn_map[char]
            if val >= 10:
                unit = val
                if num == 0:
                    total += unit
                else:
                    total += num * unit
                num = 0
            else:
                num = val
        else:
            return -1
    return total + num


def detect_chapters(text_by_page: Dict[int, str]) -> List[Tuple[int, int]]:
    chapters = []
    current_start = None
    last_detected_page = -1  # 防止同页重复识别

    sorted_pages = sorted(text_by_page.keys())

    for page_num in sorted_pages:
        text = text_by_page[page_num]

        if is_probable_toc_page(text):
            continue

        lines = [l.strip() for l in text.split("\n")[:8] if l.strip()]  # 只看页首

        for line in lines:
            if len(line) > 60:
                continue

            for pattern in CHAPTER_REGEXES:
                m = re.match(pattern, line)
                if not m:
                    continue

                if re.match(r'^卷\s*[一二三四五六七八九十0-9]+$', line):
                    # 这是“卷二 / 卷三”这种卷标题，不是章节
                    print(f"[忽略卷标题] 第{page_num}页 -> {line}")
                    continue

                # 防止同一页重复触发
                if page_num == last_detected_page:
                    continue

                # 新章节开始
                if current_start is not None:
                    chapters.append((current_start, page_num - 1))

                current_start = page_num
                last_detected_page = page_num

                print(f"[章节识别] 第{page_num}页 -> {line}")
                break
            else:
                continue
            break

    if current_start is not None:
        chapters.append((current_start, sorted_pages[-1]))

    return chapters


def split_pdf_by_auto_chapters(
    ctx: TaskContext,
    input_path: str,
    output_path: str,
    chapters_per_unit: int = 5
):
    """
    PDF 自动拆分任务（智能识别章节，每N章为一个单元）

    :param ctx: TaskContext
    :param input_path: 输入 PDF
    :param output_path: 输出 PDF 基础路径
    :param chapters_per_unit: 每个单元包含的章节数，默认为5
    """

    try:
        chapters_per_unit = validate_chapters_per_unit(chapters_per_unit)
        ctx.report_progress(0, "开始自动识别章节结构")
        
        # 提取PDF文本
        ctx.report_progress(10, "提取PDF文本内容")
        text_by_page = extract_text_from_pdf(input_path)
        
        # 智能识别章节
        ctx.report_progress(30, "智能识别章节边界")
        chapters = detect_chapters(text_by_page)
        
        if len(chapters) == 0:
            raise ValueError("未能识别到章节结构，请检查PDF文档格式")
        
        ctx.report_progress(50, f"成功识别 {len(chapters)} 个章节")
        
        # 使用现有的按章节拆分功能
        split_pdf_by_chapters(ctx, input_path, output_path, chapters, chapters_per_unit)
        
    except TaskCancelledError:
        ctx.report_done("操作已取消", None)
    
    except Exception as e:
        ctx.report_error(str(e))


def split_pdf_by_single_pages(
    ctx: TaskContext,
    input_path: str,
    output_path: str,
):
    """
    PDF 拆分任务（拆成单页）

    :param ctx: TaskContext
    :param input_path: 输入 PDF
    :param output_path: 输出 PDF 基础路径
    """

    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)

        if total_pages <= 0:
            raise ValueError("PDF 无页面")

        base_name = os.path.splitext(output_path)[0]
        ctx.report_progress(0, "开始拆分为单页")

        for page_index in range(total_pages):
            ctx.check_cancelled()

            writer = PdfWriter()
            writer.add_page(reader.pages[page_index])

            file_path = f"{base_name}_page_{page_index + 1}.pdf"
            with open(file_path, "wb") as f:
                writer.write(f)

            progress = (page_index + 1) / total_pages * 100
            ctx.report_progress(
                progress,
                f"处理中：第 {page_index + 1} 页 / 共 {total_pages} 页"
            )

        ctx.report_progress(100, "拆分完成")
        ctx.report_done("已拆分为单页 PDF 文件", f"{base_name}_page_1.pdf")

    except TaskCancelledError:
        ctx.report_done("操作已取消", None)

    except Exception as e:
        ctx.report_error(str(e))


def split_pdf_by_chapters(
    ctx: TaskContext,
    input_path: str,
    output_path: str,
    chapter_ranges: List[Tuple[int, int]],
    chapters_per_unit: int = 5
):
    """
    PDF 拆分任务（按章节范围，每N章为一个单元）

    :param ctx: TaskContext
    :param input_path: 输入 PDF
    :param output_path: 输出 PDF 基础路径
    :param chapter_ranges: [(chapter_start_page, chapter_end_page)]，每个元组表示一章的页码范围
    :param chapters_per_unit: 每个单元包含的章节数，默认为5
    """

    try:
        chapters_per_unit = validate_chapters_per_unit(chapters_per_unit)
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)

        if len(chapter_ranges) == 0:
            raise ValueError("章节范围为空")

        # 验证所有章节范围的有效性
        for i, (start, end) in enumerate(chapter_ranges):
            if start < 1 or end > total_pages or start > end:
                raise ValueError(f"第{i+1}章页码范围无效: {start}-{end}")

        ctx.report_progress(0, "开始按章节拆分 PDF")

        # 计算总工作量（用于进度）
        total_units = len(chapter_ranges)
        completed_units = 0

        # 按每N章为一个单元进行分组
        unit_chapters = []
        current_unit = []
        for i, chapter in enumerate(chapter_ranges):
            current_unit.append(chapter)
            # 当单元达到指定大小或处理到最后一个章节时，添加到单元列表
            if len(current_unit) == chapters_per_unit:
                unit_chapters.append(current_unit.copy())
                current_unit = []
        # 处理最后一个可能不足N章的单元
        if current_unit:
            unit_chapters.append(current_unit.copy())

        # 处理每个单元
        output_files = []
        for unit_index, unit in enumerate(unit_chapters):
            ctx.check_cancelled()

            # 计算当前单元的页码范围
            unit_start_page = unit[0][0]
            unit_end_page = unit[-1][1]
            unit_start_chapter = unit_index * chapters_per_unit + 1
            unit_end_chapter = min((unit_index + 1) * chapters_per_unit, len(chapter_ranges))

            # 创建新的PDF文件
            writer = PdfWriter()

            # 添加当前单元的所有页面
            for chapter_start, chapter_end in unit:
                for page_index in range(chapter_start - 1, chapter_end):
                    writer.add_page(reader.pages[page_index])

                completed_units += 1
                progress = completed_units / total_units * 100
                ctx.report_progress(
                    progress,
                    f"处理中：第 {completed_units} 章 / 共 {total_units} 章"
                )

            # 生成输出文件名
            base_dir = os.path.dirname(output_path)
            base_name = os.path.splitext(os.path.basename(output_path))[0]
            if unit_start_chapter == unit_end_chapter:
                unit_output_name = f"第{unit_start_chapter}章_{base_name}.pdf"
            else:
                unit_output_name = f"第{unit_start_chapter}-{unit_end_chapter}章_{base_name}.pdf"
            unit_output_path = os.path.join(base_dir, unit_output_name)

            # 写入文件
            with open(unit_output_path, "wb") as f:
                writer.write(f)

            output_files.append(unit_output_path)

        ctx.report_progress(100, "拆分完成")
        if chapters_per_unit == 1:
            ctx.report_done("已按章节拆分 PDF 文件", output_files[0] if output_files else None)
        else:
            ctx.report_done(f"已按每{chapters_per_unit}章为一个单元拆分 PDF 文件", output_files[0] if output_files else None)

    except TaskCancelledError:
        ctx.report_done("操作已取消", None)

    except Exception as e:
        ctx.report_error(str(e))
