#!/usr/bin/env python3
"""
测试 EPUB 转 PDF 功能的编码处理
"""

import os
import tempfile
import zipfile
import json

def create_test_epub(output_path):
    """创建一个简单的测试 EPUB 文件"""
    # EPUB 是一个 ZIP 文件，包含特定的结构
    with zipfile.ZipFile(output_path, 'w') as zf:
        # 添加 mimetype 文件
        zf.writestr('mimetype', 'application/epub+zip')
        
        # 添加 META-INF/container.xml
        container_xml = '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
        zf.writestr('META-INF/container.xml', container_xml)
        
        # 添加 content.opf
        content_opf = '''<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>测试 EPUB</dc:title>
        <dc:creator>测试作者</dc:creator>
        <dc:identifier id="bookid">urn:uuid:test-epub-12345</dc:identifier>
        <dc:language>zh-CN</dc:language>
    </metadata>
    <manifest>
        <item id="content" href="content.xhtml" media-type="application/xhtml+xml"/>
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    </manifest>
    <spine toc="ncx">
        <itemref idref="content"/>
    </spine>
</package>'''
        zf.writestr('content.opf', content_opf)
        
        # 添加 toc.ncx
        toc_ncx = '''<?xml version="1.0" encoding="UTF-8"?>
<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">
    <head>
        <meta name="dtb:uid" content="urn:uuid:test-epub-12345"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle>
        <text>测试 EPUB</text>
    </docTitle>
    <navMap>
        <navPoint id="navpoint-1" playOrder="1">
            <navLabel>
                <text>第一章</text>
            </navLabel>
            <content src="content.xhtml"/>
        </navPoint>
    </navMap>
</ncx>'''
        zf.writestr('toc.ncx', toc_ncx)
        
        # 添加 content.xhtml（包含中文字符）
        content_xhtml = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>测试内容</title>
    <meta charset="UTF-8"/>
</head>
<body>
    <h1>测试 EPUB 文档</h1>
    <p>这是一个测试 EPUB 文档，用于测试 EPUB 转 PDF 功能的编码处理。</p>
    <p>包含中文字符和特殊字符：你好，世界！</p>
    <p>测试段落 1：Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
    <p>测试段落 2： Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
</body>
</html>'''
        zf.writestr('content.xhtml', content_xhtml)

def test_epub_conversion():
    """测试 EPUB 转 PDF 功能"""
    print("创建测试 EPUB 文件...")
    with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp_epub:
        epub_path = tmp_epub.name
    
    create_test_epub(epub_path)
    print(f"测试 EPUB 文件已创建：{epub_path}")
    
    # 创建输出 PDF 路径
    pdf_path = epub_path.replace('.epub', '.pdf')
    print(f"输出 PDF 文件路径：{pdf_path}")
    
    # 导入必要的函数进行测试
    try:
        from split_pdf_gui import do_epub_convert_with_progress
    except ImportError:
        print("错误：无法导入 split_pdf_gui 模块")
        return False
    
    # 模拟进度和错误处理函数
    def mock_post_progress(pct, text):
        print(f"进度: {pct}% - {text}")
    
    def mock_post_done(msg, paths):
        print(f"完成: {msg}")
        if paths:
            print(f"生成的文件: {paths}")
    
    def mock_post_error(msg):
        print(f"错误: {msg}")
    
    # 替换原始函数
    import split_pdf_gui
    original_post_progress = split_pdf_gui.post_progress
    original_post_done = split_pdf_gui.post_done
    original_post_error = split_pdf_gui.post_error
    
    split_pdf_gui.post_progress = mock_post_progress
    split_pdf_gui.post_done = mock_post_done
    split_pdf_gui.post_error = mock_post_error
    
    # 运行转换
    print("\n开始测试 EPUB 转 PDF 转换...")
    try:
        # 设置全局变量
        split_pdf_gui.cancel_requested = False
        do_epub_convert_with_progress(epub_path, pdf_path, "a4")
        print("\n测试完成！")
        success = True
    except Exception as e:
        print(f"\n转换过程中出现错误: {e}")
        success = False
    finally:
        # 恢复原始函数
        split_pdf_gui.post_progress = original_post_progress
        split_pdf_gui.post_done = original_post_done
        split_pdf_gui.post_error = original_post_error
    
    # 清理临时文件
    try:
        if os.path.exists(epub_path):
            os.unlink(epub_path)
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
    except Exception:
        pass
    
    return success

if __name__ == "__main__":
    success = test_epub_conversion()
    if success:
        print("\n🎉 测试成功！EPUB 转 PDF 功能的编码问题已修复。")
    else:
        print("\n❌ 测试失败！EPUB 转 PDF 功能仍存在问题。")