# -*- coding: utf-8 -*-
"""07_build_paper.py —— 生成期末论文 DOCX（按课程模板排版）。

输出：docs/纽约黄色出租车运营分析与需求预测.docx
运行：py -X utf8 scripts/07_build_paper.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
FIG = ROOT / "outputs" / "figures"
DASH = ROOT / "outputs" / "dashboard"
TAB = ROOT / "outputs" / "tables"
ASSETS = ROOT / "assets"
OUT = DOCS / "纽约黄色出租车运营分析与需求预测.docx"

TITLE = "纽约黄色出租车运营分析与需求预测"
SUBTITLE = "——基于 TLC 2024 年公开行程数据"
AUTHOR = "作者：孔梦"
SCHOOL = "（嘉兴大学 数据科学学院）"

ABSTRACT = (
    "本文使用纽约市出租车与礼宾车管理局（TLC）公开的 2024 年黄色出租车行程记录，完成取数、清洗、"
    "建模与可视化。原始数据 12 个月共 4116.97 万行、660.9 MiB，清洗后保留 3919.26 万行（95.20%），"
    "覆盖 261 个分区，总收入 11.05 亿美元。分析采用 SARIMAX、K-Means、梯度提升、ABC/波士顿矩阵、"
    "STL 与 OD 集中度六类方法。结果显示：需求在 17—19 时形成晚高峰，周末整体后移；JFK 与 LaGuardia"
    "以 7.7% 的行程贡献 20.4% 的收入；信用卡行程平均小费率为 22.25%，机场行程的慷慨小费比例比非机场"
    "低 22.4 个百分点；SARIMAX 在 11 月验证集 MAPE 为 10.44%，12 月测试集为 20.44%，主要误差来自"
    "圣诞周。据此提出分时分区调度、机场运力保障、长尾区域培育与支付数字化建议。"
)
KEYWORDS = "城市交通；需求预测；SARIMAX；K-Means；交互式大屏"

CN_FONT = "宋体"
HEI = "黑体"
KAI = "楷体_GB2312"
EN_FONT = "Times New Roman"


# --------------------------------------------------------------------------- 基础排版
def set_run(run, cn=CN_FONT, size=12, bold=False, color=None, en=EN_FONT):
    run.font.name = en
    run._element.rPr.rFonts.set(qn("w:eastAsia"), cn)
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def shade(element, color: str):
    tcPr = element._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def para_shade(p, color="F5F7FA"):
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    pPr.append(shd)


def set_page(section, left=3.175, right=3.175, top=2.54, bottom=2.54):
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(left)
    section.right_margin = Cm(right)
    section.top_margin = Cm(top)
    section.bottom_margin = Cm(bottom)
    section.header_distance = Cm(1.5)
    section.footer_distance = Cm(1.5)


def body_para(doc, text, indent=True, size=12, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
              before=0, after=0, line=1.5, cn=CN_FONT):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = align
    pf.line_spacing = line
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    if indent:
        pf.first_line_indent = Pt(size * 2)
    r = p.add_run(text)
    set_run(r, cn=cn, size=size, bold=bold)
    return p


def h1(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.space_before = Pt(12)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.5
    pf.keep_with_next = True
    r = p.add_run(text)
    set_run(r, cn=HEI, size=12, bold=True)
    return p


def h2(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.first_line_indent = Pt(0)
    pf.space_before = Pt(8)
    pf.space_after = Pt(4)
    pf.line_spacing = 1.5
    pf.keep_with_next = True
    r = p.add_run(text)
    set_run(r, cn=HEI, size=12, bold=True)
    return p


def h3(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.first_line_indent = Pt(0)
    pf.space_before = Pt(4)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.5
    pf.keep_with_next = True
    r = p.add_run(text)
    set_run(r, cn=HEI, size=12, bold=True)
    return p


def caption(doc, text, above=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.space_before = Pt(6 if above else 3)
    pf.space_after = Pt(3 if above else 8)
    pf.line_spacing = 1.0
    if above:
        pf.keep_with_next = True
    r = p.add_run(text)
    set_run(r, cn=CN_FONT, size=10.5, bold=True)
    return p


def figure(doc, name, cap, width=15.0):
    path = FIG / name
    if not path.exists():
        path = DASH / name
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.space_before = Pt(6)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.0
    pf.keep_with_next = True
    p.add_run().add_picture(str(path), width=Cm(min(width, 14.2)))
    caption(doc, cap)


def table(doc, cap, headers, rows, font=9.0, widths=None, first_left=True):
    if cap:
        caption(doc, cap, above=True)
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblPr = t._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    if widths:
        total = sum(widths)
        if total > 14.5:
            widths = [w * 14.5 / total for w in widths]
        tblW = tblPr.find(qn("w:tblW"))
        if tblW is None:
            tblW = OxmlElement("w:tblW")
            tblPr.append(tblW)
        tblW.set(qn("w:type"), "dxa")
        tblW.set(qn("w:w"), str(int(sum(widths) / 2.54 * 1440)))
        for i, w in enumerate(widths):
            t.columns[i].width = Cm(w)
    hdr = t.rows[0]
    trPr = hdr._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    trPr.append(tbl_header)
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(str(h))
        set_run(r, cn=CN_FONT, size=font, bold=True, color=(0, 0, 0))
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cell = cells[i]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if (i == 0 and first_left) else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_before = Pt(1.5)
            p.paragraph_format.space_after = Pt(1.5)
            r = p.add_run(str(v))
            set_run(r, cn=CN_FONT, size=font)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Cm(w)
    # 防止表格跨页断开：行内禁止拆分，除末行外与下一行同页
    for ri, row in enumerate(t.rows):
        trPr = row._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
        if ri < len(t.rows) - 1:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.keep_with_next = True
    gap = doc.add_paragraph()
    gap.paragraph_format.space_after = Pt(2)
    gap.paragraph_format.line_spacing = 1.0
    return t


def code_block(doc, text):
    for line in text.strip("\n").split("\n"):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.line_spacing = 1.0
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.left_indent = Cm(0.3)
        para_shade(p, "F2F4F7")
        r = p.add_run(line if line else " ")
        set_run(r, cn="Consolas", size=8.5, en="Consolas")


def add_header_footer(section):
    section.header.is_linked_to_previous = False
    section.footer.is_linked_to_previous = False
    hp = section.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    hr = hp.add_run("商业数据分析")
    set_run(hr, cn=KAI, size=9)
    pPr = hp._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "000000")
    pBdr.append(bottom)
    pPr.append(pBdr)

    fp = section.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run()
    set_run(run, cn=CN_FONT, size=9)
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)


def restart_numbering(section, start=1):
    pg = OxmlElement("w:pgNumType")
    pg.set(qn("w:start"), str(start))
    section._sectPr.append(pg)


def clear_numbering(section):
    for pg in section._sectPr.findall(qn("w:pgNumType")):
        section._sectPr.remove(pg)


# --------------------------------------------------------------------------- 封面与前置页
def cover(doc):
    section = doc.sections[0]
    set_page(section, left=2.75, right=2.5, top=1.9, bottom=2.0)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(14)
    logo = ASSETS / "logo.png"
    if logo.exists():
        p.add_run().add_picture(str(logo), width=Cm(8.4))

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(14)
    r = p.add_run("商业数据分析")
    set_run(r, cn=KAI, size=36, bold=True)

    fields = [
        ("题　　目：", TITLE),
        ("学　　院：", "数据科学学院"),
        ("专业班级：", "大数据241"),
        ("学　　号：", "2024459985106"),
        ("姓　　名：", "孔梦"),
        ("完成日期：", "2026年11月1日"),
    ]
    for label, value in fields:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.left_indent = Cm(2.4)
        pf.line_spacing = 1.45
        pf.space_after = Pt(3)
        pf.tab_stops.add_tab_stop(Cm(13.2))
        pPr = p._p.get_or_add_pPr()
        for tag in ("w:autoSpaceDE", "w:autoSpaceDN"):
            el = OxmlElement(tag)
            el.set(qn("w:val"), "0")
            pPr.append(el)
        r1 = p.add_run(label)
        set_run(r1, cn=KAI, size=14)
        r2 = p.add_run(value)
        set_run(r2, cn=KAI, size=14)
        r2.underline = True
        r3 = p.add_run("\t")
        set_run(r3, cn=KAI, size=14)
        r3.underline = True

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    grading_table(doc)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("数 据 科 学 学 院")
    set_run(r, cn=CN_FONT, size=14)


def front_matter(doc):
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    set_page(sec, left=2.75, right=2.5, top=2.5, bottom=2.5)
    sec.header.is_linked_to_previous = False
    sec.footer.is_linked_to_previous = False
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run()
    set_run(run, cn=CN_FONT, size=9)
    f1 = OxmlElement("w:fldChar")
    f1.set(qn("w:fldCharType"), "begin")
    ins = OxmlElement("w:instrText")
    ins.set(qn("xml:space"), "preserve")
    ins.text = " PAGE "
    f2 = OxmlElement("w:fldChar")
    f2.set(qn("w:fldCharType"), "end")
    run._r.append(f1)
    run._r.append(ins)
    run._r.append(f2)
    restart_numbering(sec, 1)

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.0
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run(TITLE)
    set_run(r, cn=HEI, size=16, bold=True)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run("作者：孔梦")
    set_run(r, cn=CN_FONT, size=10.5)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(18)
    r = p.add_run(SCHOOL)
    set_run(r, cn=CN_FONT, size=10.5)

    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.first_line_indent = Pt(24)
    pf.line_spacing = 1.5
    pf.space_after = Pt(10)
    r = p.add_run("摘要：")
    set_run(r, cn=HEI, size=14, bold=True)
    r = p.add_run(ABSTRACT)
    set_run(r, cn=CN_FONT, size=12)

    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.first_line_indent = Pt(24)
    pf.line_spacing = 1.5
    r = p.add_run("关键词：")
    set_run(r, cn=HEI, size=14, bold=True)
    r = p.add_run(KEYWORDS)
    set_run(r, cn=CN_FONT, size=12)


# --------------------------------------------------------------------------- 正文
# -*- coding: utf-8 -*-
# 第 1—3 章（按课程模板重组）


def chapter1(doc):
    h1(doc, "1  引言")
    h2(doc, "1.1  研究背景")
    body_para(doc,
              "黄色出租车由纽约市出租车与礼宾车管理局（Taxi and Limousine Commission，TLC）统一监管，"
              "执行政府定价和分区运营，行程由计价器自动记录，口径统一、覆盖全城。2024 年全年约完成"
              "4117 万次载客，日均 10.7 万次。在网约车分流、远程办公改变通勤结构的背景下，这一体量"
              "仍是城市交通的重要组成部分。")
    body_para(doc,
              "行业同时面临四个问题：需求在小时、星期和季节尺度上波动明显；收入集中在机场和曼哈顿"
              "核心区；机场行程客单价高，小费率反而偏低；节假日和大型活动会造成需求骤降或脉冲。"
              "靠经验排班很难同时应对这四件事。")
    body_para(doc,
              "TLC 自 2014 年起按月公开行程记录，字段包括上下车时间、分区、里程、支付方式、车费、"
              "小费与附加费，并已匿名化。数据全量、免费、许可清晰，适合做商业分析。本文以此为基础，"
              "把行程记录转化为可执行的运营判断。")

    h2(doc, "1.2  研究目的")
    body_para(doc,
              "本文围绕需求、收入、服务与预测提出五个问题：需求在时间和空间上如何分布；收入集中在"
              "哪些区域和支付方式；小费受什么因素影响、能否提前预测；短期需求能否预测、异常日能否"
              "识别；上述结论能落到哪些调度和服务动作。")
    body_para(doc,
              "方法上，描述统计与热力图刻画现状，帕累托、ABC 和波士顿矩阵分析收入结构，K-Means 划分"
              "区域功能，梯度提升识别小费行为，SARIMAX 与 STL 负责预测和异常识别。六类方法按"
              "“现状—结构—归因—预测—行动”的顺序展开，最终形成一套可复现的运营分析流程。")
    body_para(doc,
              "技术路线分五步：从 TLC 官方 CloudFront 地址下载 12 个月度 Parquet 和分区边界，逐文件"
              "记录 SHA-256、行数与字段；按月流式清洗，派生时长、速度、小费率、机场标记等变量；用"
              "六类模型完成预测、分群、分类、分层与异常识别；从时间、空间、支付、距离、小费五个维度"
              "做探索与可视化；最后生成静态图、交互大屏和商业建议。所有图表和指标均可由脚本重跑。")
    table(doc, "表 1-1  技术路线、关键产出与对应章节",
          ["阶段", "主要工作", "关键产出", "章节"],
          [
              ["数据获取", "官方 HTTPS 下载、SHA-256 校验、行数与字段审计", "12 个 parquet、raw_audit.json", "第 2 章"],
              ["清洗治理", "流式清洗、派生变量、聚合表、分层样本", "3919 万行分析底表、10 余张聚合表", "第 3 章"],
              ["模型分析", "SARIMAX、K-Means、梯度提升、ABC/BCG、STL、OD", "预测区间、4 类区域、AUC 0.771", "第 4 章"],
              ["探索与可视化", "时间、空间、支付、距离、小费五维分析", "33 张静态图、六组件大屏", "第 5 章"],
              ["案例与建议", "结果解读、分时调度、机场与长尾策略", "5 条建议、优先级表", "第 6 章"],
          ], font=9.0, widths=[2.4, 6.4, 5.4, 1.6])
    body_para(doc,
              "原始数据 4116.97 万行、660.9 MiB，清洗后保留 3919.26 万行，覆盖 261 个有上车记录的分区、"
              "500 条高频 OD 走廊和 366 个自然日。代码约 2000 行，按配置、下载、清洗、分析、可视化、"
              "大屏、截图和论文生成拆分，依赖写入 requirements.txt。")

    h2(doc, "1.3  研究意义")
    body_para(doc,
              "对运营方，本文把“按天配车”细化为“按功能区、按时段配车”，给出早晚班与夜班的覆盖范围、"
              "机场排队与返程匹配的做法、长尾区域的预约与巡游组合，以及支付数字化的优先级。每条建议"
              "都对应一个可观测指标，便于在周会中复盘，而不是停留在定性判断。")
    body_para(doc,
              "对行业与监管，公开数据加可复现基线，能量化假日冲击、机场依赖和收入集中度，为运力政策、"
              "价格听证和服务考核提供参考。对方法实践，本文把描述统计、分层、聚类、分类、时序预测和"
              "异常识别放在同一份数据上交叉验证，并披露现金小费不可观测等口径限制，说明“结论成立的前"
              "提”与结论本身同样重要。")
    body_para(doc,
              "全文共 7 章：第 1 章说明背景、目的与意义；第 2 章介绍数据源、合规获取与数据集结构；"
              "第 3 章给出清洗、转换与整合规则；第 4 章完成模型选型、参数设定与验证；第 5 章做探索"
              "分析、图表复现、业务模型图与交互大屏；第 6 章解读结果并提出商业建议；第 7 章总结结论、"
              "局限与 AI 使用情况。")


def chapter2(doc):
    h1(doc, "2  数据准备与预处理")
    h2(doc, "2.1  数据源介绍")
    body_para(doc,
              "核心数据为 TLC 发布的《Yellow Taxi Trip Records》2024 年 1—12 月数据集[1]，托管于 TLC"
              "官方数据页（https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page），文件通过"
              "纽约市政府 CloudFront 域名（https://d37ci6vzurychx.cloudfront.net）直接下载。数据按月"
              "更新，每月一个 Parquet，字段结构稳定。",
              align=WD_ALIGN_PARAGRAPH.LEFT)
    body_para(doc,
              "辅助数据包括 taxi_zone_lookup.csv（263 个分区的编号、行政区、名称与服务类型）和官方"
              "分区边界 Shapefile（EPSG:2263，重投影为 WGS84 后转 GeoJSON），用于地图与大屏的离线"
              "绘制。两者均来自 TLC 官方页面，不含个人信息。")
    body_para(doc,
              "只选黄色出租车，是因为其定价和运营规则最统一、分区覆盖最完整。混入网约车会因计价和"
              "调度机制不同而污染需求结构；只看机场行程，又会丢失城市内部的通勤信息。")
    body_para(doc,
              "12 个文件合计 41,169,720 行、693,001,713 字节（660.9 MiB），平均每月 343.1 万行，"
              "月度行数在 282.6 万（8 月）至 383.4 万（10 月）之间。单文件 47.7—62.3 MiB，普通笔记本"
              "可分块读取。")
    _file_table(doc)
    body_para(doc,
              "每个文件 19 个字段，分为时间、位置、行程、金额和支付五组，不含姓名、电话、车牌等直接"
              "标识；分区编号需通过查询表映射为地名。核心字段及派生用途见表 2-2。")
    table(doc, "表 2-2  核心字段说明",
          ["字段", "类型", "含义", "用途"],
          [
              ["pickup / dropoff", "datetime", "上车、下车时间", "派生日期、小时、时长"],
              ["PULocationID / DOLocationID", "int16", "上、下车分区编号（1—263）", "区域聚合、OD 分析"],
              ["distance_mi", "float32", "行程里程（英里）", "距离分布、速度、小费模型"],
              ["duration_min", "float32", "行程时长（分钟）", "时长分布、异常判定"],
              ["speed_mph", "float32", "平均速度（英里/小时）", "拥堵识别、异常标记"],
              ["fare / tip / tolls / total", "float32", "车费、小费、路桥费、总金额（美元）", "收入结构、小费率"],
              ["payment_type", "int16", "支付方式编码（1=信用卡）", "支付结构、小费口径"],
              ["RatecodeID", "int16", "费率代码（2/3=机场固定价）", "机场识别、小费模型"],
              ["airport", "bool", "是否机场相关（费率或分区）", "机场对比、KPI"],
              ["borough_pu / zone_pu", "category", "上车行政区、分区名称", "区域汇总、地图"],
              ["tip_rate / generous", "float / bool", "小费率及是否≥25%", "小费分布与分类"],
              ["cluster_name / abc_tier", "category", "功能类型、ABC 分层", "分区画像、调度建议"],
          ], font=8.2, widths=[4.6, 2.2, 6.2, 4.2])

    h2(doc, "2.2  合规获取方式")
    body_para(doc,
              "下载使用 Python 标准库 urllib 发起 HTTPS GET 请求，按 TLC 命名规则拼接 12 个 CloudFront "
              "URL[2]，设置超时、断点续传和三次重试。下载后逐个计算 SHA-256，并用 pyarrow 核对行数和"
              "字段。整个过程不解析 HTML、不模拟登录、不携带 Cookie、不绕过访问控制，属于课程允许的"
              "“官方下载文件”方式，不是爬虫。Selenium 只用于对本地 Streamlit 大屏截图，不参与数据采集。")
    body_para(doc,
              "审计结果写入 outputs/tables/raw_audit.json，包含来源页、下载基址、许可、获取时间"
              "（2026-10-30 23:17:09）、分析窗口、时区，以及每个文件的 URL、字节数、SHA-256、行数和"
              "字段。文件被替换或截断都能通过哈希发现，指标有疑问也能回溯到月份和字段。")
    body_para(doc,
              "分析窗口固定为 2024-01-01 00:00:00 至 2024-12-31 23:59:59，时区采用数据自带的"
              "America/New_York；跨年行程按上车时间归属。这样与 TLC 的月度口径一致，也避免时区换算"
              "造成小时分布偏移。")

    h2(doc, "2.3  数据来源合规声明")
    body_para(doc,
              "数据集由纽约市政府公开发布，按 TLC 数据页和 NYC Open Data 条款使用，按原样提供。本次"
              "获取日期为 2026 年 10 月 30 日，许可为公开数据使用条款。本文仅用于课程学习与非商业研究，"
              "注明来源与获取日期，不转售、不再分发原始文件；仓库只保留派生指标、聚合表和图表。")
    body_para(doc,
              "TLC 已做匿名化：不含姓名、证件号和联系方式，位置只到出租车分区，时间精确到秒但没有"
              "可关联到个人的订单号。本文不做再识别，也不把分区数据与人口、住房等微观数据做个体匹配。"
              "合规上坚持三条：不使用爬虫、不绕过反爬；不用于商业用途或二次分发；完整披露来源、许可"
              "和处理方式。完整声明见《数据来源与使用合规声明》。")

    h2(doc, "2.4  数据集概述")
    body_para(doc,
              "数据组织为星型结构：行程明细表是事实表，分区查询表和分区边界是维度表，日、分区、OD 等"
              "聚合表由事实表派生。事实表以 VendorID、上下车时间和上下车分区构成联合业务键，"
              "PULocationID、DOLocationID 分别外接 taxi_zone_lookup 的 LocationID；分区边界以"
              "LocationID 与查询表一一对应。")
    table(doc, "表 2-3  数据表结构与关联",
          ["表", "类型", "主键/业务键", "关联与用途"],
          [
              ["yellow_tripdata_2024-01…12", "事实表", "VendorID+上下车时间+上下车分区", "外接分区维度，派生全部指标"],
              ["taxi_zone_lookup", "维度表", "LocationID", "分区→行政区、名称、服务类型"],
              ["taxi_zones（Shapefile）", "空间维度", "LocationID", "分区边界，用于地图与大屏"],
              ["daily / daily_zone_payment", "派生表", "date（+分区+支付）", "趋势、预测、大屏联动"],
              ["zone_stats / od_pairs", "派生表", "LocationID / 起讫对", "ABC、BCG、聚类、OD 分析"],
          ], font=8.4, widths=[4.8, 2.2, 4.8, 5.2])
    body_para(doc,
              "清洗前先做质量画像。时间上有 56 条记录的上车时间落在 2024 年之外，少量记录下车早于"
              "上车或时长超过 4 小时。空间上 PULocationID 与 DOLocationID 取值为 1—265，其中 264、"
              "265 为未知分区，另有记录落在查询表之外。金额上有负总额、负车费、负小费，也有总额为 0 "
              "但里程为正的记录。")
    body_para(doc,
              "缺失主要有两类。passenger_count、RatecodeID、congestion_surcharge 和 Airport_fee "
              "各有 4,091,232 行为空，占 9.94%，且位置高度一致，推测与部分车载设备或代存代发订单"
              "有关；payment_type=0 占 9.40%，RatecodeID=99 占 10.51%，属于有值但语义不明。两类都"
              "保留并单独标注，避免系统性丢失订单。")
    body_para(doc,
              "里程为 0 或超过 100 英里的记录不多，但会拉偏均值；按里程/时长计算，速度超过 60 mph 的"
              "记录有 3,038 条（0.008%），多为 GPS 漂移或时间戳错位。另有两类口径问题：total_amount "
              "含小费、路桥费和附加费，fare_amount 只是计价车费；tip_amount 只对信用卡可靠，现金小费"
              "通常不记录。后文指标都建立在这些区分之上。")


def _file_table(doc):
    import json
    audit = json.loads((TAB / "raw_audit.json").read_text(encoding="utf-8"))
    rows = []
    for f in audit["files"]:
        rows.append([f["month"], f"{f['rows']:,}", f"{f['bytes'] / 1024 / 1024:.1f}",
                     f["sha256"][:12] + "…"])
    rows.append(["合计", f"{audit['totals']['rows']:,}",
                 f"{audit['totals']['bytes'] / 1024 / 1024:.1f}", "12 个文件"])
    table(doc, "表 2-1  2024 年黄色出租车月度文件与审计信息",
          ["月份", "行数", "大小/MiB", "SHA-256 前 12 位"],
          rows, font=8.5, widths=[3.0, 4.2, 3.2, 5.4])


def chapter3(doc):
    h1(doc, "3  数据清洗与治理")
    h2(doc, "3.1  数据清洗")
    body_para(doc,
              "清洗前先把问题分成四类：逻辑不可能（时长为负、下车早于上车、分区不在查询表内）、"
              "数值极端但可能真实（80 英里的机场长途、4 小时的城市拥堵）、编码型缺失（四个字段同时"
              "为空、支付方式为 0、计价代码为 99）和口径差异（总额含小费而车费不含、现金小费不可"
              "观测）。四类问题分别对应剔除、保留并标注、单独分组和在指标定义中说明。")
    body_para(doc,
              "分类是为了避免清洗过度。把 20 英里以上的记录全部删掉，会低估机场行程的收入贡献；把 "
              "tip_amount=0 全部视为缺失，会移除大量真实的“不给小费”行为，反而高估小费率。规则尽量"
              "保留真实行为，只剔除无法解释的记录。")
    body_para(doc,
              "规则共七条。时间窗保留 2024 年内的记录，剔除 56 条跨年或时钟错误；时长保留 1—240 "
              "分钟，剔除 524,922 条零值、负值或超过 4 小时的记录；距离保留 0.01—100 英里，剔除 "
              "777,918 条零里程、负里程或明显错误的长里程；金额要求 total_amount>0、fare_amount≥0、"
              "tip_amount≥0，剔除 733,884 条负值或零值；分区要求上下车均在 1—263 内，剔除 425,655 "
              "条未知分区；以 VendorID、上下车时间、上下车分区和总额为联合键，删除 9 条完全重复；"
              "速度超过 60 mph 的 3,038 条只打标，不删除，在速度分析和地图中排除。")
    table(doc, "表 3-1  清洗规则、命中行数与处理方式",
          ["规则", "判定条件", "命中行数", "处理"],
          [
              ["时间窗", "上车时间不在 2024-01-01 至 2024-12-31", "56", "剔除"],
              ["行程时长", "1 分钟 ≤ 时长 ≤ 240 分钟", "524,922", "剔除越界记录"],
              ["行程距离", "0.01 英里 ≤ 里程 ≤ 100 英里", "777,918", "剔除越界记录"],
              ["金额", "总额>0，车费≥0，小费≥0", "733,884", "剔除负值/零值"],
              ["分区", "上下车分区均在 1—263", "425,655", "剔除未知分区"],
              ["重复", "联合键完全一致", "9", "保留首条"],
              ["速度", "速度 > 60 mph", "3,038", "打标，不删除"],
              ["缺失字段", "四个字段同时为空", "4,091,232", "保留，分析时单独分组"],
          ], font=8.8, widths=[2.6, 7.2, 3.2, 2.8])
    body_para(doc,
              "规则之间存在重叠，一条记录可能同时时长为 0、里程为 0、金额为 0。各条规则的命中数之和"
              "约 246.2 万，实际净剔除 197.7 万。审计文件同时记录两者，避免混淆。清洗后保留 "
              "39,192,643 行，保留率 95.20%；分月保留率在 94.71%（9、10 月）至 95.93%（4 月）之间，"
              "没有某个月份的系统性缺失。被剔除的多为零时长、零里程、零金额和未知分区记录，长途、"
              "短途、现金与信用卡行程均保留。")

    h2(doc, "3.2  数据转换")
    body_para(doc,
              "类型统一在读取阶段完成：VendorID、payment_type、RatecodeID、PULocationID 和 "
              "DOLocationID 转为 int16，月份、星期、小时转为 int8，金额、里程、时长和速度转为 "
              "float32，分区名称与行政区转为 category。这样既压缩内存，也避免后续聚合时因字符串"
              "编码不一致产生重复分组。")
    body_para(doc,
              "日期对齐以 pickup 为准，拆出 date、month、weekday、hour 四个时间维度；dropoff 只用于"
              "计算时长，跨年行程按上车时间归属。分区编号通过 taxi_zone_lookup 映射为名称和行政区，"
              "行政区缺失的记录归入“未知”，不参与行政区对比，但仍计入总量。")
    body_para(doc,
              "派生变量包括 duration_min、distance_mi、speed_mph、tip_rate（小费/车费，仅信用卡且"
              "车费>0）、generous（tip_rate≥25%）、is_card、airport（上下车分区为 JFK/LaGuardia，"
              "或计价代码为 JFK/Newark）、time_band、is_weekend、is_rush。派生规则写入 "
              "config.py，字段含义同步到 docs/data_dictionary.md。")

    h2(doc, "3.3  数据整合")
    body_para(doc,
              "41M 行一次性载入会占用数十 GB 内存。本文用 pandas[14] 按月流式处理：每次只读一个 "
              "Parquet，完成类型"
              "转换、清洗、派生和聚合后立即写出结果并释放内存；原始明细不落地，只保留聚合表和 120 万"
              "行分层样本。描述统计与模型输入都来自全量聚合，而非样本外推。")
    body_para(doc,
              "另抽取 120 万行分层样本：每月随机 10 万行，随机种子为 42 加月份序号。样本只用于分布图、"
              "散点图和小费模型的训练/测试，总量、收入与分区排名一律使用全量聚合表。涉及样本的图表"
              "均在标题或注释中注明。")
    body_para(doc,
              "整合结果是一张明细样本加多张聚合表。日粒度表用于趋势和预测，日×分区×支付表用于"
              "大屏联动，小时×行政区表用于热力图，分区表用于 ABC/BCG 和聚类，OD 表用于走廊分析，"
              "支付/计价/行政区表用于结构对比。每张表保留行程量、收入、车费、小费、里程、时长、"
              "信用卡行程和机场行程等基础度量。")
    table(doc, "表 3-2  主要输出表与用途",
          ["表名", "行数", "粒度", "主要用途"],
          [
              ["daily", "366", "日", "需求趋势、SARIMAX、STL 异常"],
              ["monthly", "12", "月", "月度节奏、收入结构"],
              ["daily_zone_payment", "332,606", "日×分区×支付", "大屏联动、分区下钻"],
              ["daily_hour", "8,783", "日×小时", "时段曲线、热力图"],
              ["daily_hour_borough", "36,127", "日×小时×行政区", "行政区时段对比"],
              ["zone_stats", "261", "分区", "ABC、BCG、聚类、地图"],
              ["od_pairs", "500", "上车分区×下车分区", "OD 走廊与集中度"],
              ["payment_stats", "5", "支付方式", "支付结构与小费"],
              ["trips_sample", "1,200,000", "行程", "分布图、小费模型"],
          ], font=8.8, widths=[4.6, 2.6, 4.6, 5.0])
    body_para(doc,
              "聚合表以 Parquet 或 CSV 写出，Parquet 用 snappy 压缩，CSV 用 UTF-8。字段名统一为英文"
              "蛇形，单位写入 README 和字段字典。清洗规则、随机种子和表间对应关系写入 clean_audit.json，"
              "便于从原始文件重新得到同一张表。")
    body_para(doc,
              "最终底表包含 39,192,643 次行程、11.05 亿美元总收入、261 个有上车记录的分区。平均每次"
              "行程收入 28.20 美元，平均里程 3.37 英里，平均时长 16.87 分钟；信用卡行程占 76.11%，"
              "机场相关行程占 9.99%；信用卡行程平均小费率 22.25%。这些指标与 TLC 公开的年度汇总"
              "量级一致。清洗剔除了约 4.8% 的记录，零里程、零金额的短途和异常订单占比更高，对“极短"
              "行程”的估计可能略偏低；现金小费不可观测，相关结论不外推到现金行程。")

# -*- coding: utf-8 -*-
# 第 4 章 商业分析模型（按课程模板重组）


def chapter4(doc):
    h1(doc, "4  商业分析模型")
    h2(doc, "4.1  模型选型")
    body_para(doc,
              "本章围绕四个经营问题组织模型：未来一周需要多少车、哪些区域该配什么运力、哪些因素影响"
              "小费、哪些日子和走廊需要预案。SARIMAX 做日需求预测[3-6]，K-Means 做区域功能分群[7-8]，"
              "梯度提升和逻辑回归做小费分类[9,10]，ABC/帕累托和波士顿矩阵做收入分层[15]，STL 做异常"
              "识别[11]，OD 集中度刻画网络结构。")
    body_para(doc,
              "选型遵循三条原则。第一，先可解释、再追精度：运营排班需要知道“为什么高”，而不是只有"
              "一个预测值，因此保留 SARIMAX 的周周期项和假日外生变量，保留逻辑回归作为小费模型基线。"
              "第二，模型要匹配数据结构：日需求是单序列、强周周期，适合季节 ARIMA；分区需求是 261 条"
              "短序列，逐区建模样本不足，先用聚类归纳功能类型；小费是二分类且特征存在非线性交互，"
              "用梯度提升[13]。第三，描述性方法与预测性方法分开评价，ABC/BCG 看口径与业务含义，预测与"
              "分类看回测误差。")
    body_para(doc,
              "评价口径有三条：预测按时间切分，1—11 月训练、12 月测试，另设 11 月验证集；分类报告"
              "AUC、精确率、召回率和 Brier，不只看准确率；描述性模型强调口径透明、阈值可解释。预测"
              "精度以 MAPE 为主、RMSE 和 R² 为辅，MAPE 的定义与局限参照 Hyndman 和 Koehler[12]。")
    table(doc, "表 4-1  本文模型体系与主要结论",
          ["业务问题", "方法", "主要输入", "评价指标", "主要结论"],
          [
              ["日需求预测", "SARIMAX", "日行程量、节假日哑变量", "MAPE、RMSE、R²", "11 月 10.44%，12 月 20.44%"],
              ["区域功能分群", "K-Means + PCA", "24 小时份额、周末/机场/支付/客单价", "轮廓系数", "k=4，轮廓系数 0.286"],
              ["小费行为", "梯度提升 / 逻辑回归", "车费、时段、区域、里程、费率代码", "AUC、F1、Brier", "AUC 0.771 对 0.747"],
              ["收入分层", "ABC / 帕累托", "分区收入", "累计收入份额", "前 22 区贡献 69.83%"],
              ["区域组合", "波士顿矩阵", "上下半年增速、收入份额", "四象限", "现金牛贡献 96.83%"],
              ["异常日识别", "STL（周期 7）", "日行程量", "残差 z 值", "12 天异常，均为负向"],
              ["网络结构", "OD 集中度", "起讫分区对", "CR20", "CR20 仅 6.13%"],
          ], font=8.4, widths=[2.6, 3.1, 4.5, 2.9, 4.3])
    body_para(doc,
              "模型目标不是最高拟合精度，而是回答具体经营问题。SARIMAX 的 12 月误差较大，但残差诊断"
              "显示周周期已充分提取，这个不完美的结果反而说明节假日外生冲击的重要；小费模型 AUC "
              "0.771，则说明个体差异仍有大量不可解释部分，不宜过度依赖算法定价。")

    h2(doc, "4.2  参数与阈值设定依据")
    body_para(doc,
              "参数分两类：一类由统计准则确定，如 SARIMAX 阶数、聚类数、树模型轮数；另一类由业务"
              "惯例和分布特征确定，如 ABC 分界、慷慨小费阈值、异常 z 值。两类都做敏感性检查，避免"
              "结论依赖某个任意取值。")
    table(doc, "表 4-2  关键参数与阈值",
          ["模型/环节", "参数或阈值", "取值", "设定依据"],
          [
              ["SARIMAX", "非季节/季节阶数", "(1,1,2)(1,0,1,7)", "11 月验证集 MAPE 最小（10.44%），AIC 辅助"],
              ["SARIMAX", "外生变量", "法定假日、感恩节周", "假日需求塌陷无法由周周期解释"],
              ["K-Means", "聚类数 k", "4", "轮廓系数 0.286，且四类均可命名、可落地"],
              ["K-Means", "建模样本", "年行程≥2,000 次的 179 区", "排除低频长尾对中心的拉扯"],
              ["分类模型", "正类阈值", "小费率≥25%", "分布第二密集区起点，对应“满意档”"],
              ["分类模型", "切分与种子", "70%/30%，seed=42", "课程要求，保证可复现"],
              ["ABC", "累计收入分界", "70% / 90%", "帕累托分层的常用分界"],
              ["波士顿矩阵", "象限分界", "增速中位数 18.09%，份额中位数 0.0222%", "中位数不受机场极值影响"],
              ["STL", "周期与异常阈值", "7 天；|z|≥2.5", "周周期；双侧约 1.2% 的尾部概率"],
              ["OD", "走廊保留数", "Top 500", "覆盖 50.12% 的行程，兼顾可读性"],
          ], font=8.4, widths=[3.4, 4.2, 4.6, 5.0])
    body_para(doc,
              "聚类数的选择最能体现“统计与运营的折中”。k=5 的轮廓系数降到 0.271，k=6 回升到 0.285，"
              "但会拆出两个只有个位数分区、无法命名的小类，排班无法执行；k=4 的四类在 24 小时曲线、"
              "机场份额和周末份额上都有清晰边界，因此选 4。慷慨小费的 25% 阈值也做过 20%、25%、30% "
              "的对比：20% 正样本过多、区分度低，30% 正样本降至三成、召回不足，25% 与支付界面的"
              "“满意档”一致。异常 z 值取 2.5 而不是 3，是因为假日塌陷的样本只有十几个，阈值过高会"
              "漏掉 12 月 26 日、11 月 29 日等次日效应；取 2.5 后识别的 12 天全部可解释为假日或假日"
              "前后。")

    h2(doc, "4.3  模型计算与验证")
    h3(doc, "4.3.1  需求预测：SARIMAX")
    body_para(doc,
              "日行程量有明显周周期：工作日高、周末低，周五和周六夜间反弹。以 7 天为季节周期，构建"
              "SARIMAX(p,1,q)(P,0,Q,7)，加入法定假日和感恩节周两个外生哑变量。差分阶数取 1，季节"
              "差分取 0，候选模型在 11 月验证集上以 MAPE 为主、AIC 为辅比较。")
    table(doc, "表 4-3  SARIMAX 候选模型前 5 名（1—10 月拟合，11 月验证）",
          ["排名", "非季节阶数", "季节阶数", "验证 MAPE/%", "AIC"],
          [
              ["1", "(1, 1, 2)", "(1, 0, 1, 7)", "10.44", "6,168.5"],
              ["2", "(1, 1, 1)", "(1, 0, 1, 7)", "10.46", "6,220.0"],
              ["3", "(2, 1, 1)", "(1, 0, 1, 7)", "10.46", "6,222.0"],
              ["4", "(1, 1, 2)", "(1, 0, 0, 7)", "11.27", "6,243.3"],
              ["5", "(2, 1, 1)", "(1, 0, 0, 7)", "11.27", "6,247.3"],
          ], font=8.8, widths=[1.6, 3.6, 3.8, 3.4, 3.0])
    body_para(doc,
              "最终模型为 SARIMAX(1,1,2)(1,0,1,7)，含假日和感恩节周两个外生变量，AIC 为 6,807.9。"
              "11 月验证集 MAPE 为 10.44%，优于其余 11 个候选；Ljung-Box 检验 p 值为 0.157，在 5% "
              "显著性水平下不能拒绝残差白噪声，说明周周期和短期自相关已被提取。拟合与预测曲线、"
              "逐日误差和实际—预测散点见图 5-17 至图 5-19。")
    body_para(doc,
              "12 月测试集 MAPE 为 20.44%，MAE 为 21,064.5 次，RMSE 为 23,414.7 次，R² 仅 0.276。"
              "31 天中有 25 天绝对百分比误差超过 10%，12 天超过 20%，4 天超过 30%；12 月 25 日实际"
              "51,491 次、预测 87,774 次，误差 70.47%；26 日、24 日、29 日分别为 51.53%、36.69%、"
              "30.61%，集中在圣诞—新年假期。12 月实际总行程 347.48 万次，预测 329.06 万次，总量"
              "低估 5.30%，但总量接近掩盖了日度误差。")
    body_para(doc,
              "预测同时输出 95% 置信区间。12 月下旬区间明显变宽，24—31 日的区间宽度多在 15 万—21 万"
              "次，下界接近 0；实际值虽仍落在区间内，但点预测高估 30%—70%，过宽的区间也失去排班"
              "指导意义。这说明模型并未整体失效，而是无法识别假日周的需求塌陷：周周期项只能学习"
              "星期几的平均水平，圣诞落在工作日时仍按普通工作日外推，因而高估。")

    h3(doc, "4.3.2  区域功能分群：K-Means")
    body_para(doc,
              "区域分群的目标是识别需求节律相同的功能区。以年行程量不低于 2,000 次的 179 个分区为"
              "样本，构造 28 个特征：24 小时出发份额、周末份额、机场份额、信用卡渗透率和对数平均车费。"
              "标准化后用 PCA 降到二维可视化，聚类本身在高维空间进行。k=4 时轮廓系数 0.286，k=5 "
              "为 0.271，k=6 为 0.285 但多出两个难以命名的小类，故取 k=4。")
    table(doc, "表 4-4  四类区域的功能画像",
          ["类型", "分区数", "行程份额", "收入份额", "周末份额", "22—2 时份额", "机场份额", "峰值时点"],
          [
              ["核心商业区型", "51", "86.07%", "87.26%", "28.03%", "13.3%", "6.4%", "18 时"],
              ["夜间活力型", "15", "9.76%", "8.35%", "51.54%", "39.3%", "4.3%", "0 时"],
              ["早高峰通勤型", "63", "2.22%", "2.12%", "23.74%", "7.1%", "1.3%", "7 时"],
              ["通勤休闲混合型", "50", "1.80%", "2.06%", "33.89%", "18.2%", "9.3%", "7 时"],
          ], font=8.8, widths=[3.5, 2.0, 2.4, 2.4, 2.4, 2.8, 2.3, 2.2])
    body_para(doc,
              "核心商业区型 51 个分区，贡献 86.07% 的行程和 87.26% 的收入，覆盖曼哈顿中城、上东区、"
              "上西区及两个机场；18 时峰值，周末份额 28.03%，机场份额 6.4%。夜间活力型 15 个分区，"
              "贡献 9.76% 的行程，周末份额 51.54%，22 时至次日 2 时占 39.3%，0 时峰值，集中在西村、"
              "东村、下东区。早高峰通勤型 63 个分区，行程份额 2.22%，7 时峰值，周末份额 23.74%，"
              "机场份额 1.3%；通勤休闲混合型 50 个分区，行程份额 1.80%，7 时峰值但曲线平缓，机场"
              "份额 9.3%。")
    body_para(doc,
              "验证分两层。统计上，k=4 的轮廓系数 0.286 在候选值中最高，且四类中心在 28 维空间中"
              "分离度稳定；业务上，把类别放回地图后呈连续片区而非随机散点，核心区沿曼哈顿中轴和"
              "机场分布，夜间活力型集中在下城，通勤型沿布鲁克林和皇后区外围呈半环。PCA 投影、雷达图、"
              "24 小时曲线和空间分布见图 5-20 至图 5-23。")

    h3(doc, "4.3.3  小费行为：梯度提升分类")
    body_para(doc,
              "小费是司机收入的一部分，也是服务质量和支付意愿的观测窗口。本文只用信用卡行程，把"
              "“小费率≥25%”定义为慷慨小费，构造二分类。样本 914,737 条，正样本 55.56%，按 70%/30% "
              "划分，训练 640,315 条、测试 274,422 条。")
    body_para(doc,
              "特征包括车费、里程、时长、乘客数、小时、星期、月份、上车行政区、机场标记、费率代码和"
              "时段哑变量。逻辑回归作为可解释基线，HistGradientBoosting 作为非线性模型，两者使用"
              "相同特征和切分。树数量、学习率和叶子数用 3 折交叉验证确定，随机种子 42。")
    table(doc, "表 4-5  小费模型性能对比（测试集）",
          ["模型", "AUC", "准确率", "精确率", "召回率", "F1", "Brier"],
          [
              ["HistGradientBoosting", "0.771", "75.54%", "71.91%", "91.86%", "80.67%", "0.178"],
              ["LogisticRegression", "0.747", "—", "—", "—", "—", "—"],
          ], font=8.8, widths=[5.0, 2.0, 2.3, 2.3, 2.3, 2.0, 2.0])
    body_para(doc,
              "梯度提升 AUC 为 0.771，比逻辑回归高 0.024；准确率 75.54%，精确率 71.91%，召回率"
              "91.86%，F1 80.67%，Brier 0.178。召回率高于精确率，模型倾向于把可能慷慨的行程判为"
              "正类，符合“宁可多提示、不漏高意愿乘客”的场景。Brier 0.178 说明概率校准仍有改进空间，"
              "用于个体级定价需要额外校准。ROC 曲线与特征重要性见图 5-24、图 5-25。")

    h3(doc, "4.3.4  收入分层：ABC 与波士顿矩阵")
    body_para(doc,
              "ABC 分层按分区收入从高到低排序，以累计 70%、90% 为界：A 类前 22 个分区贡献 69.83%，"
              "B 类 17 个贡献 19.54%，C 类 222 个仅贡献 10.64%。A 类既有 JFK、LaGuardia，也有中城、"
              "上东区等高频核心区；B 类多为曼哈顿外围和皇后区西部；C 类是覆盖广、单价低、频次低的"
              "长尾。区域数量呈倒三角，收入却呈正三角，资源不能按分区数量平均分配。")
    body_para(doc,
              "波士顿矩阵引入增长维度：横轴为下半年相对上半年的行程增速，纵轴为全年收入份额，以增速"
              "中位数 18.09%、份额中位数 0.0222% 为界。四象限的规模差异极大，现金牛 67 个分区贡献"
              "96.83% 的收入，明星 44 个贡献 2.14%，问题 67 个贡献 0.62%，瘦狗 44 个贡献 0.39%。")
    table(doc, "表 4-6  区域组合矩阵汇总",
          ["象限", "分区数", "行程量", "收入/亿美元", "收入份额"],
          [
              ["现金牛", "67", "38,182,648", "10.70", "96.83%"],
              ["明星", "44", "695,337", "0.24", "2.14%"],
              ["问题", "67", "196,540", "0.07", "0.62%"],
              ["瘦狗", "44", "113,391", "0.04", "0.39%"],
          ], font=8.8, widths=[3.0, 2.4, 3.6, 3.2, 3.0])

    h3(doc, "4.3.5  异常识别与 OD 网络")
    body_para(doc,
              "需求异常既可能是风险，也可能是机会。用 STL 对日行程量分解，周期 7，稳健拟合，残差 z "
              "绝对值≥2.5 为异常。全年识别 12 个异常日，全部为负向，包括 12 月 25 日（z=-6.37）、"
              "11 月 28 日感恩节（z=-6.20）、7 月 4 日（z=-5.33）、11 月 29 日（z=-5.00）、12 月"
              "26 日（z=-4.66）等。异常点几乎都在法定假日或假日前后，没有显著的正向异常，说明 2024 "
              "年的需求峰值仍在趋势和季节项范围内，假日造成的需求塌陷才是真正的离群事件。")
    body_para(doc,
              "OD 网络刻画从哪里到哪里。全年最繁忙的 20 条走廊仅承担 6.13% 的行程，前 100 条承担"
              "18.59%，前 500 条承担 50.12%；单条最大的上东区南→上东区北占 0.70%。与收入集中度"
              "相比，OD 网络更分散，没有一条走廊不可替代，需求是面状分布加局部走廊。")
    table(doc, "表 4-7  Top 5 起讫（OD）走廊",
          ["排名", "起点→终点", "行程量", "份额", "平均车费/美元"],
          [
              ["1", "上东区南→上东区北", "275,689", "0.70%", "15.74"],
              ["2", "上东区北→上东区南", "237,646", "0.61%", "16.16"],
              ["3", "上东区南→上东区南", "181,842", "0.46%", "13.86"],
              ["4", "上东区北→上东区北", "177,532", "0.45%", "13.11"],
              ["5", "中城核心→上东区南", "129,680", "0.33%", "17.48"],
          ], font=8.8, widths=[1.6, 7.0, 3.0, 2.2, 3.4])
    body_para(doc,
              "六个模型相互印证：SARIMAX 证明周周期是需求的主结构，但假日冲击无法由历史模式外推；"
              "K-Means 把城市划为四类功能区；小费模型说明车费和时段是支付意愿的主要可观测因素；"
              "ABC 与波士顿矩阵揭示核心区和机场的现金流地位；STL 识别出 12 个假日异常日；OD 集中度"
              "表明网络分散、走廊集中度低。下一章把这些结果转化为图表和大屏。")

# -*- coding: utf-8 -*-
# 第 5 章（上）：数据探索性分析


def chapter5(doc):
    h1(doc, "5  Python 数据分析与可视化")
    h2(doc, "5.1  数据探索性分析")
    body_para(doc,
              "探索分析回答四个问题：需求有多少、何时发生；收入从哪里来、谁在支付；行程有多长、"
              "多快；空间上如何分布。所有指标来自全量聚合表，分布图使用 120 万行分层样本，并在图注"
              "中注明口径。")

    h3(doc, "5.1.1  总量与时间节奏")
    body_para(doc,
              "2024 年需求呈“春升、夏降、秋高、冬稳”的节奏。1—2 月日均约 9.2 万—9.5 万次，3 月起"
              "回升，5 月达到 357.1 万次；7—8 月回落至 293.1 万和 282.6 万次；10 月以 363.1 万次"
              "成为全年最高月。第四季度合计 1057.4 万次，占全年 27.0%，是最重要的经营窗口。")
    figure(doc, "fig01_月度行程量.png", "图 5-1  2024 年黄色出租车月度行程量")
    body_para(doc,
              "月度需求与城市活动强度更相关，而不是随气温单调变化。3—6 月商务、旅游和学期节奏抬升"
              "需求，7—8 月居民外出度假而回落，10 月会议季、返校和旅游叠加形成峰值。按气温加减车的"
              "直觉并不成立，排班应跟随事件日历。")
    body_para(doc,
              "366 天的均值为 107,084 次，中位数 106,990 次，标准差 18,087 次，变异系数 16.9%；5% "
              "分位 76,430 次，95% 分位 134,217 次；最低 51,491 次（12 月 25 日），最高 152,423 次"
              "（12 月 14 日）。峰谷比接近 3:1，按日均值配车在高峰期必然短缺、在节假日必然过剩。")
    figure(doc, "fig02_日行程量趋势.png", "图 5-2  日行程量与 7 日移动平均（含异常日标记）")
    body_para(doc,
              "7 日移动平均在 3—6 月缓慢上行，7—8 月下探，9—10 月再次抬升，12 月中旬达到全年高点"
              "后急速坠落。12 月 14 日的 152,423 次并非孤立脉冲，前后一周都高于移动平均，节前购物、"
              "聚会和旅游形成了持续的需求高原；12 月 25 日的 51,491 次则是全年唯一的断崖，与圣诞"
              "当天商业活动停摆一致。")
    body_para(doc,
              "工作日 7—9 时出现通勤早峰，17—19 时出现晚峰；周末早峰消失，晚峰后移并延续至 0—2 时。"
              "17—19 时合计贡献 20.19% 的行程，18 时单小时占 7.12%；4—5 时合计仅占 1.19%，是运力"
              "最闲置的时段；15—16 时占 12.32%，构成下午的次高峰。")
    figure(doc, "fig03_时段星期热力图.png", "图 5-3  星期×小时平均行程量热力图")
    body_para(doc,
              "热力图的深色带集中在两处：周一至周五的 7—9 时和 17—19 时，以及周五、周六的 22 时至"
              "次日 2 时。前者是通勤，后者是夜间消费和娱乐。周日早高峰最弱，但晚间需求仍高，说明"
              "周末不是简单的低需求，而是需求时点整体后移。把周末当低谷减车，会错过夜间的高价值"
              "订单。")
    figure(doc, "fig22_工作日周末时段对比.png", "图 5-4  工作日与周末的分时需求对比")
    body_para(doc,
              "工作日曲线呈 M 形双峰，周末呈单峰后移；两条曲线在 10—16 时几乎重合，说明日间需求的"
              "主力是旅游、购物和跨区办事，而非通勤。早班应覆盖 6—10 时，晚班覆盖 16—20 时，夜班"
              "重点覆盖周五、周六的 22 时至次日 2 时，不必平均分配。")

    h3(doc, "5.1.2  收入结构与支付方式")
    body_para(doc,
              "全年总收入 11.05 亿美元，其中计价车费 7.61 亿美元（68.88%）、小费 1.31 亿美元（11.87%）、"
              "路桥费 0.22 亿美元（1.97%），其余 17.28% 为拥堵费、机场费、MTA 税和改善附加费。单次"
              "行程平均收入 28.20 美元，平均计价车费 19.42 美元。小费占比接近 12%，是司机收入的重要"
              "组成部分。")
    figure(doc, "fig04_月度收入构成.png", "图 5-5  月度收入构成（车费、小费、路桥费与其他）", width=12.0)
    body_para(doc,
              "收入结构的月度变化主要由量驱动。10 月行程量最高，收入也最高（1.05 亿美元）；1—2 月"
              "量低，收入约 0.76 亿—0.77 亿美元。小费占比 1 月最高（12.51%）、8 月最低（11.50%）。"
              "7—8 月收入下降，平均车费反而上升（7 月 28.42、8 月 28.61 美元），下降的主要是短途、"
              "高频的城市内部行程，长途机场行程相对稳定。")
    body_para(doc,
              "支付方式高度集中：信用卡 2983.1 万次（76.11%）、现金 517.2 万次（13.20%）、未知/弹性"
              "计价 368.4 万次（9.40%）、争议 36.3 万次（0.93%）、免收费 14.2 万次（0.36%）。信用卡"
              "行程平均记录小费 4.30 美元，现金仅 0.0002 美元。这不是现金乘客不给小费，而是现金小费"
              "无法被计价器记录；基于 tip_amount 的分析必须排除现金或单独说明。")
    figure(doc, "fig09_支付方式占比.png", "图 5-6  支付方式结构（按行程量）", width=12.6)
    body_para(doc,
              "信用卡占绝对主导，说明黄色出租车电子化程度较高；但仍有 13.20% 的现金和 9.40% 的"
              "未知/弹性计价，后者可能来自企业账户、代存代发或设备未上传，不能简单归为现金。地域"
              "差异也明显：曼哈顿信用卡占比 76.6%，布朗克斯仅 53.8%，这直接影响后文观测到的小费率"
              "差异。")
    table(doc, "表 5-1  支付方式结构与观测小费",
          ["支付方式", "行程量", "占比", "平均记录小费/美元", "说明"],
          [
              ["信用卡", "29,830,984", "76.11%", "4.30", "小费可观测，分析主力"],
              ["现金", "5,171,773", "13.20%", "0.0002", "小费不可观测"],
              ["未知/弹性计价", "3,684,062", "9.40%", "0.79", "可能为企业账户/代存代发"],
              ["争议", "363,497", "0.93%", "0.01", "金额异常，单独分组"],
              ["免收费", "142,327", "0.36%", "0.01", "免费或补偿行程"],
          ], font=8.8, widths=[3.4, 3.2, 2.2, 3.6, 5.0])

    h3(doc, "5.1.3  距离、时长与速度")
    body_para(doc,
              "黄色出租车是典型的短途高频业态。平均里程 3.37 英里，中位数仅 1.80 英里，25% 分位"
              "1.07 英里，95% 分位 13.90 英里；平均时长 16.87 分钟，中位数 13.03 分钟，95% 分位"
              "43.45 分钟。均值明显高于中位数，是机场长途和跨区行程拉动的结果。典型行程是 1—2 "
              "英里、10—15 分钟，收入却高度依赖少数长途。")
    figure(doc, "fig05_行程时长分布.png", "图 5-7  行程时长分布（截尾至 90 分钟）")
    body_para(doc,
              "时长分布右偏单峰，大量行程集中在 5—20 分钟，25 分钟后迅速衰减，30—45 分钟处仍有一个"
              "对应机场与跨区行程的小峰。分布没有明显双峰，城市短途与机场长途是连续过渡而非两个"
              "独立市场；但长尾很厚，95% 分位达到 43 分钟，排班不能只按平均 17 分钟估算周转。")
    figure(doc, "fig07_行程距离分布.png", "图 5-8  行程距离分布（截尾至 20 英里）")
    body_para(doc,
              "距离分布比时长更陡。1 英里以内和 1—3 英里的行程占绝大多数，10 英里以上迅速变稀，"
              "15—20 英里处出现一个与机场相关的小峰。距离的右偏程度高于时长，说明长途更多体现为"
              "里程而非时间：机场高速距离远，但单位时间效率高于市区拥堵，这也解释了机场行程平均"
              "车费高、平均时长却不一定最长。")
    figure(doc, "fig31_速度分布.png", "图 5-9  平均速度分布（剔除 >60 mph 的异常记录）", width=13.2)
    body_para(doc,
              "平均速度中位数 9.29 mph，均值 10.84 mph；9.54% 的行程低于 5 mph，属于严重拥堵；"
              "超过 40 mph 的仅占 0.29%，多为机场高速或深夜畅通路段。市中心车速与步行速度接近，"
              "距离对时间的解释力有限，调度必须同时考虑时段和路段拥堵。短途高价与长途高速是两种"
              "不同的收益模式，不能用单一“每英里收入”衡量。")
    body_para(doc,
              "速度分析也暴露了数据质量问题：少数记录按里程/时长计算超过 100 mph，最高 1213 mph，"
              "显然是 GPS 漂移或时间戳错位。本文对 3,038 条超过 60 mph 的记录打标，在速度分布和"
              "地图中排除，但保留在总量与收入统计中，避免低估总量。")

    h3(doc, "5.1.4  小费行为")
    body_para(doc,
              "信用卡行程平均小费率 22.25%，中位数 26%，25% 分位 20%，75% 分位 31%，95% 分位 40%。"
              "20% 处有明显尖峰，对应纽约出租车常见的默认选项；25%—30% 形成第二个密集区。把"
              "“小费率≥25%”定义为慷慨小费，信用卡行程中 55.56% 属于慷慨，多数乘客愿意支付高于"
              "默认档的小费。")
    figure(doc, "fig10_小费率分布.png", "图 5-10  信用卡行程小费率分布")
    body_para(doc,
              "20% 是乘客的心理锚点，25% 是慷慨门槛，30% 是第二个锚点。提升小费的重点不是“要求"
              "更多”，而是把默认选项从 20% 适度上移，或在长途、优质服务后给出 25% 的提示；过度"
              "提示会引发反感。")
    figure(doc, "fig11_小费率时段曲线.png", "图 5-11  分时平均小费率与慷慨小费比例")
    body_para(doc,
              "小费率在凌晨 0—3 时最高（约 24.0%—24.2%），清晨 5—6 时最低（约 22.0%—22.4%），"
              "白天在 22.5%—23.5% 之间波动。凌晨的高小费率可能与娱乐、机场早班机等夜间场景有关，"
              "清晨的低小费率则与通勤客群、短途行程和赶时间有关。慷慨比例的分时差异更大：凌晨 2 时"
              "约 56.8%，清晨 5—6 时约 47.1%，相差近 10 个百分点。")
    figure(doc, "fig28_小费率热力图.png", "图 5-12  行政区×小时平均小费率热力图")
    body_para(doc,
              "行政区差异明显：曼哈顿几乎全天呈深色，晚间更深；皇后区中等；布鲁克林和布朗克斯偏浅。"
              "全量口径下，曼哈顿信用卡小费率 25.32%、慷慨比例 58.23%，皇后区 20.98%/33.93%，"
              "布鲁克林 7.16%/10.89%，布朗克斯 1.18%/1.75%。这组差异不能全部归因于乘客慷慨程度："
              "布朗克斯信用卡渗透率仅 53.8%，大量现金行程的小费未被记录；外围行政区的行程更短、"
              "车费更低，小费绝对值也更小。本文只解释观测口径，不把差异道德化。")
    table(doc, "表 5-2  行政区观测小费率（仅信用卡行程）",
          ["行政区", "信用卡行程", "平均小费率", "慷慨比例", "信用卡渗透率"],
          [
              ["曼哈顿", "26,823,987", "25.32%", "58.23%", "76.56%"],
              ["皇后区", "2,682,784", "20.98%", "33.93%", "76.77%"],
              ["布鲁克林", "263,312", "7.16%", "10.89%", "47.99%"],
              ["布朗克斯", "60,281", "1.18%", "1.75%", "53.81%"],
              ["斯塔滕岛", "130", "18.62%", "41.54%", "9.51%"],
          ], font=8.8, widths=[3.2, 3.4, 3.2, 3.0, 3.8])

    h3(doc, "5.1.5  区域结构与机场走廊")
    body_para(doc,
              "收入的空间集中度远高于行程量。曼哈顿以 89.39% 的行程贡献 75.46% 的收入，皇后区以"
              "8.92% 的行程贡献 22.60%，布鲁克林与布朗克斯合计不足 2%。皇后区的高收入主要来自"
              "两个机场：JFK 单区 176.6 万次行程、1.428 亿美元收入（12.92%），LaGuardia 123.4 万次、"
              "0.830 亿美元（7.51%），合计 20.43%。黄色出租车实际上存在“城市内循环”和“机场走廊”"
              "两个市场。")
    figure(doc, "fig12_区域收入帕累托.png", "图 5-13  分区收入帕累托图")
    body_para(doc,
              "帕累托曲线在头部非常陡：前 22 个分区（8.4%）贡献 69.83% 的收入，前 39 个（14.9%）"
              "贡献 89.37%，其余 222 个分区仅贡献 10.64%。这比经典二八法则更极端，原因是机场和曼哈顿"
              "核心区的高客单价叠加高密度。头部分区是必须守住的基本盘，长尾分区是可以低成本覆盖的"
              "网络，资源投入逻辑不同。")
    figure(doc, "fig14_区域收入气泡地图.png", "图 5-14  分区收入气泡地图（气泡=收入，颜色=平均车费）", width=13.2)
    body_para(doc,
              "气泡大小表示收入，颜色表示平均车费。JFK 与 LaGuardia 气泡最大、颜色最深，位于皇后区"
              "东部；曼哈顿中城与上东区形成一串中等气泡，颜色偏浅但数量密集；布鲁克林与布朗克斯的"
              "气泡小而稀疏。高收入并不等于高车费：曼哈顿核心区靠高频短途累积收入，机场靠低频长途"
              "贡献收入，两者需要不同的运力组织方式。")
    figure(doc, "fig32_行政区收入构成.png", "图 5-15  行政区收入构成（车费、小费、路桥费与其他）")
    body_para(doc,
              "曼哈顿的收入以车费和小费为主，路桥费占比低；皇后区因机场行程经过隧道、桥梁和高速，"
              "路桥费占比明显更高；布鲁克林与布朗克斯收入规模小，更依赖基础车费。机场行程的高流水"
              "不等于高净收入，路桥费、拥堵费和空驶返程都会侵蚀收益，后文因此强调看净收益而非流水。")
    figure(doc, "fig21_机场与非机场对比.png", "图 5-16  机场与非机场行程的关键指标对比")
    body_para(doc,
              "在信用卡行程口径下，机场行程平均车费 56.86 美元，非机场仅 14.96 美元；但机场行程平均"
              "小费率 21.62%，低于非机场的 25.08%，慷慨小费比例 35.40% 对 57.85%，相差 22.4 个"
              "百分点。机场行程多为固定价或协商价，乘客对总价更敏感，乘客也更可能是游客或商务客，"
              "缺少本地常客的互惠心理。机场排队时间长、返程空驶概率高，高流水未必带来高时薪。")
    body_para(doc,
              "2024 年的空间结构可以概括为“一个核心、两个机场、一圈长尾”：曼哈顿核心区提供高频、"
              "短途、稳定的现金流；JFK 与 LaGuardia 提供低频、长途、高客单价的收入脉冲；布鲁克林、"
              "布朗克斯、斯塔滕岛和皇后区非机场部分构成广覆盖、低密度的长尾。一刀切的运力或定价"
              "策略，会在其中一个市场上失灵。")

    h2(doc, "5.2  可视化模板复现")
    body_para(doc,
              "可视化不是模型的装饰，而是结论的一部分。设计遵循四条原则：一图一问，每张图只回答一个"
              "明确问题；统一配色，深蓝为主、青绿为辅、橙色强调，同类变量在不同图中保持同色；克制"
              "装饰，去掉多余网格、边框和三维效果；标注口径，凡涉及仅信用卡、已剔除异常值、Top 500 "
              "走廊等，均在图中或图注说明。")
    body_para(doc,
              "静态图用 Matplotlib 和 Seaborn，统一 200 dpi、白底、左对齐标题和中文字体；交互图用"
              "Plotly，保持相同配色和字号。图表由脚本批量生成，文件名与正文编号一一对应。")
    body_para(doc,
              "全文 33 张静态图，覆盖柱形、条形、折线、堆积柱、直方图、散点、气泡、热力图、"
              "雷达图、地图、帕累托和 ROC 等 12 类图型，另有预测扇形与残差子图；其中 14 张与第 4 章"
              "模型一一对应（图 5-17 至图 5-30）。")
    table(doc, "表 5-3  主要图型与代表图",
          ["图型", "代表图", "回答的问题", "表达要点"],
          [
              ["柱形 / 条形", "图 5-1、图 5-6、图 5-30", "总量与排名", "长度编码数值，排序后再比较"],
              ["折线", "图 5-2、图 5-17", "趋势与预测", "保留原始波动，叠加移动平均"],
              ["堆积柱", "图 5-5、图 5-15", "收入构成", "总量与结构同时呈现"],
              ["直方图", "图 5-7、图 5-8", "分布形态", "截尾离群值，保留主体形态"],
              ["散点 / 气泡", "图 5-14、图 5-27", "相关与组合", "位置、大小、颜色三重编码"],
              ["热力图", "图 5-3、图 5-12", "二维密度", "统一色阶，标注单位"],
              ["雷达图", "图 5-21", "多维画像", "类别不超过 4 类"],
              ["地图", "图 5-23、图 5-29", "空间分布", "离线边界，避免底图依赖"],
              ["帕累托", "图 5-13", "集中度", "柱形 + 累计曲线 + 80% 参考线"],
              ["ROC", "图 5-24", "分类性能", "对角线为随机基线"],
          ], font=8.4, widths=[2.6, 4.6, 4.0, 5.8])
    body_para(doc,
              "图表按总—分—异常—模型四层组织：总览层（图 5-1 至 5-4）回答需求有多少、何时发生；"
              "结构层（图 5-5 至 5-16）回答收入从哪里来、谁在支付、空间如何分布；模型层（图 5-17 至"
              " 5-30）回答未来怎么走、区域怎么分、什么因素驱动小费；异常日同时出现在图 5-2 与"
              "图 5-28。")
    body_para(doc,
              "模板复现保留标题—图例—坐标轴—数据标签的信息结构，替换为更适合城市交通的蓝绿配色。"
              "柱形图保留数值标签和零基线，折线图保留原始点和移动平均，地图保留分区边界和主要地名，"
              "热力图保留色阶图例；对照《Excel 数据可视化》的图型清单，本文覆盖 12 类、超过 10 类的"
              "复现要求，并补充预测扇形、残差图、雷达图和 ROC 等课程外图型。")

    h2(doc, "5.3  业务模型图")
    body_para(doc,
              "本节把第 4 章的模型输出转成 14 张业务图，按模型分组：需求预测 3 张、区域分群 4 张、"
              "小费模型 2 张、收入分层 2 张、异常与 OD 3 张。图只负责“看出什么”，参数与验证数值见"
              "表 4-3 至表 4-7，避免图表重复叙述。")

    h3(doc, "5.3.1  需求预测")
    figure(doc, "fig23_需求预测拟合.png", "图 5-17  SARIMAX 需求拟合与 12 月预测（95% 置信区间）")
    body_para(doc,
              "训练期拟合较好地跟踪了周内波动，12 月出现两次系统性偏离：月初实际高于预测，圣诞周"
              "远低于预测。置信区间在 12 月上旬较窄，下旬迅速张开，说明模型对假日周的不确定性有"
              "感知，但点预测仍按普通工作日外推。")
    figure(doc, "fig24_预测误差.png", "图 5-18  12 月逐日绝对百分比误差")
    body_para(doc,
              "误差呈前低后高：1—20 日多在 10%—25%，24 日之后骤然抬升，25 日达到 70%。模型并非"
              "整体失效，而是无法识别假日周的需求塌陷。周周期项只能学习星期几的平均水平，圣诞落在"
              "工作日时仍按普通工作日外推，因而高估。")
    figure(doc, "fig25_十二月实际与预测.png", "图 5-19  12 月实际与预测散点（虚线为理想预测线）", width=12.5)
    body_para(doc,
              "散点大部分位于理想线附近，右下方的几点（实际低、预测高）对应 12 月 24—26 日，左上方"
              "（实际高、预测低）对应 12 月 13—14 日节前高峰。R² 仅 0.276，日度点预测的解释力有限，"
              "按日排班必须叠加事件日历和人工修正。SARIMAX 的价值是可解释基线：普通周误差约 10%，"
              "假日周系统性高估，需要按日历下调。建议周度总量用模型、日度结构用规则，再对法定假日、"
              "感恩节和圣诞周乘修正系数。")

    h3(doc, "5.3.2  区域功能分群")
    figure(doc, "fig15_区域聚类PCA.png", "图 5-20  区域功能聚类的 PCA 投影", width=13.5)
    body_para(doc,
              "PCA 投影中，核心商业区型在右侧形成紧密的大簇，数量最多、内部差异最小；夜间活力型在"
              "左下方形成狭长带状，与其他类别明显分离；早高峰通勤型分布在右侧偏下，与核心区部分重叠；"
              "通勤休闲混合型较分散。四类分区不是人为切割，而是特征空间中自然形成的密集区与过渡带。")
    figure(doc, "fig16_聚类雷达图.png", "图 5-21  四类区域的时段结构雷达图", width=10.4)
    body_para(doc,
              "雷达图把一天分为六个时段。夜间活力型在 20—23 时和 0—3 时显著外凸，核心商业区型在"
              "16—19 时最强，早高峰通勤型在 4—7 时和 8—11 时形成双凸，通勤休闲混合型在 12—15 时"
              "相对突出。四类区域的需求指纹几乎不重叠，为差异化排班提供了依据。")
    figure(doc, "fig17_聚类时段曲线.png", "图 5-22  四类区域的 24 小时出发曲线", width=12.6)
    body_para(doc,
              "24 小时曲线进一步量化差异：核心商业区型在 7 时和 18 时双峰，夜间仍保持 4%—6% 的份额；"
              "夜间活力型 0 时达到 8.8%，随后快速下降，10 时后才回升；早高峰通勤型 7 时达到 10%，"
              "9 时后跌至 2% 以下；通勤休闲混合型最平缓，7 时和 18 时峰值均不超过 6.5%。")
    figure(doc, "fig18_聚类空间分布.png", "图 5-23  区域功能类型的空间分布", width=11.5)
    body_para(doc,
              "放回地图后，核心商业区型沿曼哈顿中轴和两个机场呈哑铃形分布；夜间活力型集中在曼哈顿"
              "下城的西村、东村和下东区；早高峰通勤型沿布鲁克林和皇后区外围呈半环状；通勤休闲混合型"
              "散布在滨水和机场周边。空间分布与功能画像一致，说明聚类结果不是统计噪声。运力配置"
              "可以从全城平均转为分区定时：核心商业区型全天保障、重点覆盖 16—20 时；夜间活力型在"
              "周五、周六 22 时至次日 2 时加车；早高峰通勤型 6—9 时定向投放，9 时后转移；通勤休闲"
              "混合型作为蓄水池，在核心区高峰补充。")

    h3(doc, "5.3.3  小费行为")
    figure(doc, "fig26_小费模型ROC.png", "图 5-24  小费模型的 ROC 曲线", width=11.2)
    body_para(doc,
              "ROC 曲线在假阳性率 0.2 处真阳性率已超过 0.6，整体位于对角线上方；逻辑回归略低，差距"
              "不大。小费行为既有线性可解释成分（车费、时段），也有非线性交互（机场×时段、区域×"
              "费率），梯度提升的优势主要来自后者。")
    figure(doc, "fig27_小费特征重要性.png", "图 5-25  小费模型的特征重要性", width=12.6)
    body_para(doc,
              "车费重要性 0.287，约为第二位“小时”的 30 倍；其后是费率代码 99、时长、星期、里程、"
              "曼哈顿上车、机场标记和晚高峰。车费一家独大不意外：小费率以车费为分母，车费越高，乘客"
              "越倾向凑整或按比例给出高于 25% 的小费；长途机场行程车费高但小费率低，金额和比例是"
              "两种心理账户。")
    body_para(doc,
              "模型不适合预测某位乘客会给多少小费并据此差别定价，AUC 0.771 不足以支撑个体决策，也有"
              "公平和合规风险。更有价值的是群体画像和服务提示：晚高峰和机场行程主动说明支付方式、"
              "提供收据，降低总价敏感；夜间和核心商业区可把默认档从 20% 上移到 25%，保留自定义入口。"
              "小费结论只适用于信用卡行程，现金小费率接近 0 不是乘客不付，而是无法观测；布朗克斯等"
              "外围行政区信用卡渗透率低，低小费率很大程度是口径造成的，不能据此做道德判断。")

    h3(doc, "5.3.4  收入分层")
    figure(doc, "fig13_区域ABC分层.png", "图 5-26  区域收入 ABC 分层", width=13.5)
    body_para(doc,
              "区域数量呈倒三角：C 类 222 个，占分区总数的 85.1%；收入却呈正三角：A 类以不到 8.5% 的"
              "分区拿走约 70% 的收入。数量与收入倒挂意味着资源不能按分区数量平均分配。A 类重点是"
              "守住运力、缩短等待、维护机场排队秩序；B 类通过调度和激励把零散需求聚成波次；C 类用"
              "预约、拼车或区域巡游维持基本可达性。")
    figure(doc, "fig29_区域机会矩阵.png", "图 5-27  区域增长—份额机会矩阵", width=14.5)
    body_para(doc,
              "JFK 与 LaGuardia 位于纵轴顶部，是典型现金牛；中城核心、上东区南、时代广场位于中上部，"
              "增速接近零甚至为负，但收入份额高；右下方的“问题”象限聚集了大量增速高、份额低的外围"
              "分区；左下方的“瘦狗”象限是增速与份额双低的长尾。明星象限几乎为空，说明 2024 年没有"
              "出现新的高增长高份额区域，增长主要来自既有核心区和机场的恢复。")
    body_para(doc,
              "策略是守住现金牛、筛选明星、改造问题、放弃瘦狗。现金牛优先保障运力和服务，避免等待"
              "过长把需求推向网约车；问题象限选择机场周边、滨水新城做小规模试点，验证预约加定点候客；"
              "瘦狗不追加固定运力，用巡游或预约覆盖。增长是下半年对上半年的环比，受季节性和基数影响，"
              "不能外推为长期趋势。")

    h3(doc, "5.3.5  异常识别与 OD 网络")
    figure(doc, "fig30_异常检测.png", "图 5-28  STL 残差法与需求异常日", width=15.0)
    body_para(doc,
              "异常点几乎都在法定假日或假日前后：感恩节、独立日、圣诞—新年周、阵亡将士纪念日周末、"
              "六月节。没有显著的正向异常，说明 2024 年的需求峰值仍在趋势和季节项范围内，假日造成的"
              "需求塌陷才是真正的离群事件。异常检测的价值不是预测假日，而是量化影响幅度，为排班和"
              "运力回收提供依据。")
    figure(doc, "fig19_OD走廊地图.png", "图 5-29  Top 20 起讫（OD）走廊", width=10.8)
    body_para(doc,
              "最粗的线是 JFK 至曼哈顿上东区的机场走廊，其次是曼哈顿内部几条短距离连线。机场—曼哈顿"
              "是唯一具有干线特征的关系，其余走廊多为相邻分区之间的短途接驳。机场走廊需要排队、载客、"
              "返程的闭环管理，曼哈顿内部走廊更适合巡游和即时派单。")
    figure(doc, "fig20_OD集中度.png", "图 5-30  Top 20 OD 的行程量", width=15.0)
    body_para(doc,
              "Top 20 走廊中，前四条都在上东区南北之间往返，第五条是中城核心至上东区南。绝大多数是"
              "曼哈顿内部的短途走廊，只有少数涉及机场。机场走廊的行程量不一定最大，但单程收入高；"
              "曼哈顿走廊行程量最大，但单程收入低，两种走廊不能用同一套考核指标。")

    h2(doc, "5.4  交互式可视化大屏")
    body_para(doc,
              "大屏用 Streamlit + Plotly 实现[16-17]，运行在本地 8508 端口，数据来自清洗阶段导出的"
              "聚合表，不直接读原始 Parquet，首屏数秒内完成。大屏包含四组筛选器、六个 KPI 卡、八个"
              "图表/下钻模块、一张明细表和 CSV 导出，超过课程要求的至少 6 个组件；全部用 Python "
              "实现，未使用 Power BI 或 Tableau。")
    table(doc, "表 5-4  大屏组件与联动关系",
          ["区域", "组件", "数据口径", "联动行为"],
          [
              ["侧边栏", "日期范围、上车行政区、支付方式、机场筛选", "日×分区×支付×机场聚合表", "驱动全部 KPI 与图表"],
              ["顶部", "6 个 KPI 卡", "筛选后汇总", "行程量、收入、单均、卡占比、机场占比、均里程"],
              ["第一行", "日趋势与异常日、支付结构环形图", "日粒度", "异常点来自 STL 结果"],
              ["第二行", "星期×小时热力图、区域气泡地图", "日×小时×行政区", "热力图仅受日期与行政区影响"],
              ["第三行", "Top 12 区域、功能类型地图", "分区聚合", "可切换排序指标"],
              ["下钻", "站点选择、5 个指标、24 小时结构、Top 10 目的地", "分区×小时、OD 表", "选择站点后联动更新"],
              ["底部", "自动洞察、区域明细表、CSV 下载", "筛选后明细", "支持导出当前筛选结果"],
          ], font=8.4, widths=[2.2, 5.4, 4.4, 5.0])
    body_para(doc,
              "联动遵循筛选—聚合—呈现的单向数据流：侧边栏的日期、行政区、支付方式和机场筛选作用于"
              "日×分区×支付聚合表，生成筛选后的行程、收入、车费、小费和里程；KPI 卡、趋势图、支付"
              "环形图、气泡地图、Top 12 和明细表都从这一份结果计算。热力图按天平均，只受日期和行政区"
              "影响；功能类型地图使用全年聚类结果，不随筛选变化，并在提示框中标注全年口径。")
    body_para(doc,
              "下钻是交互核心。选择上车站点后，右侧同时更新该站点在筛选期内的行程量、收入、平均车费、"
              "下半年环比、ABC 分层和功能类型，并给出 24 小时出发结构和 Top 10 目的地。站点不在"
              "Top 500 OD 走廊时，提示暂无可展示的目的地排行，而不是显示空白图。")
    body_para(doc,
              "大屏只依赖 outputs/tables 下的聚合表和本地 GeoJSON，不请求外部地图瓦片或 CDN，断网"
              "也能展示；图表由 Plotly 在浏览器端渲染。启动命令为 streamlit run scripts/05_dashboard.py，"
              "截图由 Selenium 以 Edge headless 完成，仅用于本地留档。")
    figure(doc, "dashboard_overview.png", "图 5-31  大屏首屏：筛选器、KPI 与总览图", width=14.2)
    body_para(doc,
              "首屏左侧为四组筛选器，默认全年、全部行政区、全部支付方式、全部行程；顶部六个 KPI 卡"
              "显示行程量 39.19 百万、总收入 11.05 亿美元、单均收入 28.20 美元、信用卡占比 76.1%、"
              "机场相关占比 10.0%、平均里程 3.37 英里。右侧上方为日趋势与异常日，下方为支付结构和"
              "星期×小时热力图。")
    figure(doc, "dashboard_full_2col.png", "图 5-32  大屏全页：从总览到下钻的完整链路", width=14.6)
    body_para(doc,
              "全页截图展示从总览到下钻的完整链路：日趋势与异常日、支付结构、星期×小时热力图、区域"
              "气泡地图、Top 12 区域、功能类型地图、站点下钻、自动洞察和区域明细表。为便于排版，"
              "截图按上下两段并排。")
    figure(doc, "dashboard_drill.png", "图 5-33  站点下钻：指标、24 小时结构与明细表", width=14.2)
    body_para(doc,
              "以 Upper East Side South 为例，筛选期内行程量 186.22 万次、收入 0.389 亿美元、平均"
              "车费 20.87 美元、下半年环比 +1.8%，ABC 分层为 A，功能类型为核心商业区型。下方左图为"
              " 24 小时出发结构，右图为 Top 10 目的地，底部为可排序、可下载的明细表。")
    body_para(doc,
              "大屏解决静态图无法回答的两个问题：换一个筛选条件结论是否成立，以及某个具体站点的情况"
              "如何。把支付方式切换为现金后，卡付小费率变为 0，支付环形图和收入结构随之变化；选择"
              "JFK 后，下钻面板显示机场属性、A 类分层和长途目的地集中度。静态图负责可出版、可引用的"
              "结论表达，交互大屏负责可探索、可下钻的分析过程，两者共享同一套数据口径和配色。")

# -*- coding: utf-8 -*-
# 第 6—7 章、参考文献与附录


def chapter6(doc):
    h1(doc, "6  商业案例分析")
    h2(doc, "6.1  案例背景")
    body_para(doc,
              "本案例的对象是纽约市黄色出租车行业。2024 年，黄色出租车完成 3,919 万次行程、11.05 亿"
              "美元收入，受 TLC 统一监管，执行政府定价与分区运营。与网约车相比，它没有动态定价和"
              "算法派单，运力组织更依赖司机的经验判断和车队的静态排班；与地铁、公交相比，它提供"
              "门到门服务，承担机场、夜间和跨区出行。远程办公削弱了工作日通勤，旅游恢复又抬高了"
              "机场和核心区的需求，行业处在“总量恢复、结构变化”的阶段。")
    body_para(doc,
              "行业的核心矛盾不是总量不足，而是时空错配。需求在时间上集中于 17—19 时和周末夜间，"
              "在空间上集中于曼哈顿核心区和两个机场，假日又会出现断崖式下跌；运力却按天、按车队"
              "平均投放。结果是一边高峰打车难、一边凌晨空驶，一边机场排队、一边外围无车。案例要"
              "回答的就是：如何用公开数据识别这种错配，并把识别结果变成排班、机场组织和支付服务"
              "上的具体动作。")
    body_para(doc,
              "分析边界需要先说明：只覆盖黄色出租车，不含网约车、绿色出租车和公共交通；小费只对"
              "信用卡行程可靠；时间跨度只有 2024 年一年。因此本文解释的是黄色出租车内部的运营规律，"
              "不把它外推为整个城市出行市场，也不把信用卡小费率当作全部乘客的支付意愿。")

    h2(doc, "6.2  结果解读")
    body_para(doc,
              "需求的时间结构是“双高峰加周末后移”。工作日 7—9 时和 17—19 时形成双峰，17—19 时"
              "贡献 20.19% 的行程，18 时单小时占 7.12%；周末早峰消失，晚峰后移并延续到 0—2 时。"
              "按全城日均配车，高峰必然短缺、凌晨必然过剩。STL 进一步识别出 12 个负向异常日，"
              "全部落在法定假日或假日前后，12 月 25 日 z 值为 -6.37，说明假日不是“略低”，而是"
              "结构性的需求塌陷，必须单独排班。")
    body_para(doc,
              "收入的空间结构是“一个核心、两个机场、一圈长尾”。曼哈顿以 89.39% 的行程贡献 75.46% "
              "的收入，皇后区以 8.92% 的行程贡献 22.60%，其中 JFK 与 LaGuardia 合计贡献 20.43%。"
              "ABC 分层显示前 22 个分区拿走 69.83% 的收入，C 类 222 个分区只贡献 10.64%；波士顿"
              "矩阵中现金牛分区贡献 96.83%，明星象限几乎为空。这说明 2024 年的增长主要来自既有"
              "核心区和机场的恢复，而不是新区域崛起。")
    body_para(doc,
              "服务与支付的结构是“高频短途、卡付主导、小费分层”。平均里程 3.37 英里、时长 16.87 "
              "分钟，信用卡占 76.11%；信用卡平均小费率 22.25%，55.56% 属于慷慨小费。机场行程车费"
              "高，但小费率 21.62%，慷慨比例比非机场低 22.4 个百分点；梯度提升 AUC 0.771，车费"
              "重要性约为第二位的 30 倍。小费差异更多来自场景和支付方式，而不是乘客“大方”与否，"
              "现金小费不可观测是最重要的口径限制。")
    body_para(doc,
              "预测与网络结构说明“模型能做什么、不能做什么”。SARIMAX 在普通周的误差约 10%，12 月"
              "因圣诞周升至 20.44%，95% 置信区间在月下旬明显变宽；模型适合做周度总量和区间，不适合"
              "直接给出假日日的点预测。OD 网络高度分散，Top 20 走廊只承担 6.13% 的行程，Top 500 "
              "才覆盖一半，机场—曼哈顿是唯一具有干线特征的走廊。没有一条走廊不可替代，意味着运力"
              "组织应以面状覆盖为主、走廊专项为辅。")
    body_para(doc,
              "把四组结果放在一起，可以得到一个统一判断：黄色出租车的问题是“在错误的时间、错误的"
              "区域投放了运力”，而不是“车不够”。这决定了建议的方向——不是简单增加车辆，而是把"
              "排班单位细化到时段和功能区，把机场从“高流水”转向“高净收益”，把长尾从“被动等待”"
              "转向“预约与巡游组合”，把小费从“压力提示”转向“锚点设计”。")

    h2(doc, "6.3  商业建议")
    h3(doc, "6.3.1  分时分区调度：从“平均配车”到“节律配车”")
    body_para(doc,
              "核心矛盾是时空错配：17—19 时贡献 20.19% 的行程，18 时单小时占 7.12%，4—5 时仅 1.19%；"
              "核心商业区型 51 个分区贡献 86.07% 的行程，夜间活力型 15 个分区贡献 9.76% 且周末份额"
              "超过一半。按全城日均配车，高峰期必然短缺、凌晨必然过剩。建议把排班单位从“天”细化"
              "到“时段×功能区”，形成三套班次：早班 6—10 时服务早高峰通勤型，晚班 16—20 时服务"
              "核心商业区型，夜班覆盖周五、周六 22 时至次日 2 时，服务夜间活力型。")
    body_para(doc,
              "执行上用预测加规则生成每日排班：先用 SARIMAX 预测下一周总量，按历史星期结构分解到日，"
              "再对法定假日、感恩节、圣诞周乘修正系数。核心商业区型目标是把高峰平均等待控制在 5 "
              "分钟以内，夜间活力型把凌晨空驶率降到 30% 以下，早高峰通勤型在 7—9 时保证每个分区"
              "至少 1 辆巡游车。指标按功能区设定，不用核心区标准考核长尾区。")

    h3(doc, "6.3.2  机场运力保障：把“高流水”变成“高净收益”")
    body_para(doc,
              "JFK 与 LaGuardia 以 7.7% 的行程贡献 20.4% 的收入，是最重要的现金流来源；但机场行程"
              "平均小费率 21.62%，低于非机场的 25.08%，司机还要承担排队、空驶返程、隧道和桥梁费用。"
              "只按流水考核，司机会倾向长途机场单，却可能在返程空驶中损失时薪。建议把机场运力管理"
              "拆成排队秩序、返程匹配和收益透明三件事。")
    body_para(doc,
              "与机场管理部门协调分区候客和电子排队，减少航站楼外的无效巡游；在到达层设置返程优先"
              "提示，把即将结束的市区订单与机场返程车辆匹配；在司机端展示扣除路桥费、拥堵费和空驶"
              "成本后的预计净收益，而不是只展示流水。")

    h3(doc, "6.3.3  长尾区域与支付数字化：不让“低密度”变成“低服务”")
    body_para(doc,
              "ABC 分层显示，C 类 222 个分区只贡献 10.64% 的收入，却覆盖大部分城市面积。完全按收入"
              "配置运力，会让外围区域陷入车少—等待久—需求流失—车更少的循环。建议对 C 类采用预约、"
              "巡游、拼车的混合模式：低密度时段以预约为主，通勤走廊设定点候客，机场周边和夜生活区"
              "保留巡游。目标不是让每个分区都盈利，而是维持可接受的可达性。")
    body_para(doc,
              "现金仍占 13.20%，未知/弹性计价占 9.40%，布朗克斯信用卡渗透率仅 53.81%。现金小费不可"
              "观测，既影响司机收入，也影响数据完整性。建议普及刷卡和非接触支付终端，对老年人和"
              "游客提供代叫车和预估总价；保留现金通道，但通过收据和短信记录行程，减少纠纷。")

    h3(doc, "6.3.4  服务与小费：用“锚点”而不是“压力”")
    body_para(doc,
              "小费率在 20% 处有明显尖峰，25%—30% 形成第二密集区；信用卡行程中 55.56% 属于慷慨"
              "小费。建议支付界面保留 20% 默认档、25% 满意档、30% 非常满意档，并允许自定义；机场"
              "和晚高峰行程主动说明路桥费、拥堵费和总价构成；夜间和核心商业区在行程结束后发送简短"
              "评价邀请，而不是反复提示小费。")
    body_para(doc,
              "要避免两个误区：把低小费率归因于乘客吝啬，忽视现金不可观测和区域收入差异；用算法对"
              "个体乘客差别定价或差别提示，既不公平，也可能违反平台规则。更稳妥的目标是把观测小费"
              "率提升 1 个百分点、慷慨比例提升 2 个百分点，通过司机培训、支付便利和总价透明实现。")

    h3(doc, "6.3.5  数据闭环：让大屏成为“周会工具”")
    body_para(doc,
              "分析链路可以固化为周度闭环：每周一更新聚合表，运行 SARIMAX 得到下一周总量预测和区间；"
              "周二结合日历和天气修正，生成分时分区排班建议；周三至周日执行并监控 KPI；下周一复盘"
              "预测误差、异常日和投诉，更新模型。大屏承担共同视图的角色，调度看时段和分区，市场看"
              "机场和夜间，管理层看收入和小费。")
    body_para(doc,
              "数据治理坚持三条：只用聚合后的分区级数据，不对个体乘客或司机再识别；公开数据更新时"
              "保留版本号和下载日期；预测区间和误差随结果一起发布，避免把点预测当确定事实。")
    table(doc, "表 6-1  建议优先级与预期效果",
          ["优先级", "措施", "数据依据", "责任方", "观察指标"],
          [
              ["高", "分时分区排班", "17—19 时占 20.19%，四类功能区", "调度", "高峰等待、空驶率"],
              ["高", "机场排队与返程匹配", "两机场贡献 20.4% 收入", "机场运营", "机场净收益、返程空驶"],
              ["中", "假日运力回收", "12 个负向异常日", "调度", "假日空驶、成本"],
              ["中", "支付终端普及", "现金 13.20%，未知 9.40%", "运营", "卡渗透率、纠纷率"],
              ["中", "小费锚点与服务培训", "卡付小费率 22.25%", "司机管理", "小费率、慷慨比例"],
              ["低", "长尾预约与拼车试点", "C 类 222 区仅 10.64% 收入", "产品", "覆盖率、满意度"],
          ], font=8.5, widths=[1.8, 4.4, 4.4, 2.6, 3.8])


def chapter7(doc):
    h1(doc, "7  结论与展望")
    h2(doc, "7.1  研究结论")
    body_para(doc,
              "本文以 TLC 2024 年黄色出租车行程记录为样本，完成 12 个月、4,116.97 万行原始数据的"
              "流式清洗，保留 3,919.26 万行（95.20%），构建需求预测、区域聚类、小费行为、收入分层、"
              "异常识别和 OD 网络六组模型，并以 33 张静态图和 1 个交互大屏呈现。全部分析可由脚本"
              "从官方原始文件重跑。")
    body_para(doc,
              "主要结论有三条。第一，需求的主结构是周周期加假日冲击：工作日双高峰、周末后移，"
              "17—19 时贡献 20.19%；12 个异常日全部为假日负向冲击，SARIMAX 在普通周 MAPE 约 10%，"
              "圣诞周升至 20.44%，预测必须叠加事件日历。第二，收入高度集中且呈双市场：曼哈顿核心区"
              "靠高频短途，两个机场靠低频长途，ABC 前 22 区贡献 69.83%，机场贡献 20.4%；现金牛"
              "分区贡献 96.83%，明星象限为空。第三，小费由车费和场景主导：信用卡平均小费率 22.25%，"
              "55.56% 属于慷慨，机场慷慨比例低 22.4 个百分点；模型可做群体画像，不适合个体定价。")
    body_para(doc,
              "方法上的收获是把“口径”放在与“精度”同等重要的位置：现金小费不可观测、总额含附加费、"
              "分区边界和时区处理都会改变结论。论文保留这些限制，并在每张图、每个指标上注明适用范围，"
              "比单纯追求更高的 AUC 或更低的 MAPE 更有价值。")

    h2(doc, "7.2  局限性与展望")
    body_para(doc,
              "数据只覆盖黄色出租车，不含网约车、绿色出租车、地铁和公交，无法刻画完整替代关系；"
              "现金小费不可观测，小费结论只适用于信用卡；时间跨度只有一年，SARIMAX 只能识别周周期，"
              "12 月假日冲击也只有一个样本，修正系数缺乏统计稳定性。")
    body_para(doc,
              "分析单元是分区和行程，不是个体乘客或司机，无法控制收入、出行目的、服务评价等变量，"
              "小费模型只能做相关性解释。收入口径为行程总金额，未扣除司机成本、平台抽成、燃油和"
              "折旧，也未纳入空驶里程，高收入分区不等于高利润分区。OD 分析只保留 Top 500 走廊，"
              "长尾结构可能被低估。")
    body_para(doc,
              "后续可从三个方向深化：多源融合，把黄色出租车、网约车、共享单车和地铁刷卡结合，构建"
              "模态竞争模型，回答需求是被抑制还是转移；分层预测，用层次时间序列或全局模型替代单序列"
              "SARIMAX，把分区、时段和假日纳入统一框架；因果与决策，在合规前提下用断点回归或倾向"
              "得分匹配评估机场排队政策、支付终端普及对小费率和等待时间的影响。")
    body_para(doc,
              "工程上可把大屏从离线聚合升级为近实时流式，接入 TLC 月度更新、天气和事件日历，形成"
              "预测—排班—监控—复盘的自动闭环；同时把预测区间和分类概率作为一等公民展示，避免把"
              "概率输出误读为确定结论。")

    h2(doc, "7.3  AI 使用披露")
    body_para(doc,
              "本作业使用了 AI 编程助手 Qoder（含代码补全与对话）。它主要出现在四类环节：环境与"
              "依赖排查，例如 Python 3.14 下 pandas、pyarrow 的兼容问题；绘图细节，例如 Matplotlib "
              "中文字体、标签重叠、图例位置；Streamlit 组件调试与离线 GeoJSON 加载；以及部分段落"
              "的语句压缩和参考文献格式检查。")
    body_para(doc,
              "关键提示词示例：（1）“按月流式读取 12 个 Parquet，过滤时长、里程、金额和分区异常，"
              "输出分月保留率与审计表，要求固定随机种子、可重复运行”；（2）“Matplotlib 中文显示为"
              "方块，x 轴标签重叠，给出不改变图意的排版调整”；（3）“把下面这段分析改得更简洁，保留"
              "全部数字和限定条件，不要添加新结论”；（4）“检查 python-docx 生成的表格跨页断裂和"
              "图片留白，给出排版参数建议”。")
    body_para(doc,
              "对 AI 输出做了三项核对：代码逐段在本地运行，指标与 outputs/tables 下的结果对齐；"
              "图表逐张检查坐标轴、单位和口径标注；文字逐段改写，删除空泛表述，数字回到原始结果"
              "复核。选题、数据来源和整体框架由本人确定；清洗规则、模型参数和商业建议在 AI 建议"
              "的基础上逐项核对后定稿。AI 提供的是实现层面的建议，可能有错误或过时用法，采纳前"
              "均经过验证。若文中有错误，责任由本人承担。")


def references(doc):
    h1(doc, "参考文献")
    refs = [
        "[1] New York City Taxi and Limousine Commission. TLC Trip Record Data[DB/OL]. "
        "(2026-10-30). https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page.",
        "[2] New York City Taxi and Limousine Commission. Yellow Taxi Trip Records 2024[DB/OL]. "
        "(2026-10-30). https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet.",
        "[3] Hyndman R J, Athanasopoulos G. Forecasting: Principles and Practice[M]. 3rd ed. "
        "Melbourne: OTexts, 2021. https://otexts.com/fpp3/.",
        "[4] Box G E P, Jenkins G M, Reinsel G C, Ljung G M. Time Series Analysis: Forecasting and "
        "Control[M]. 5th ed. Hoboken: John Wiley & Sons, 2015.",
        "[5] Moreira-Matias L, Gama J, Ferreira M, et al. Predicting taxi-passenger demand using "
        "streaming data[J]. IEEE Transactions on Intelligent Transportation Systems, 2013, 14(3): "
        "1393-1402. DOI: 10.1109/TITS.2013.2262376.",
        "[6] Ke J, Zheng H, Yang H, et al. Short-term forecasting of passenger demand under "
        "on-demand ride services: A spatio-temporal deep learning approach[J]. Transportation "
        "Research Part C: Emerging Technologies, 2017, 85: 591-608. DOI: 10.1016/j.trc.2017.10.016.",
        "[7] MacQueen J. Some methods for classification and analysis of multivariate observations[C]"
        "//Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability. "
        "Berkeley: University of California Press, 1967: 281-297.",
        "[8] Rousseeuw P J. Silhouettes: A graphical aid to the interpretation and validation of "
        "cluster analysis[J]. Journal of Computational and Applied Mathematics, 1987, 20: 53-65. "
        "DOI: 10.1016/0377-0427(87)90125-7.",
        "[9] Friedman J H. Greedy function approximation: A gradient boosting machine[J]. The Annals "
        "of Statistics, 2001, 29(5): 1189-1232. DOI: 10.1214/aos/1013203451.",
        "[10] Pedregosa F, Varoquaux G, Gramfort A, et al. Scikit-learn: Machine learning in "
        "Python[J]. Journal of Machine Learning Research, 2011, 12: 2825-2830.",
        "[11] Cleveland R B, Cleveland W S, McRae J E, et al. STL: A seasonal-trend decomposition "
        "procedure based on loess[J]. Journal of Official Statistics, 1990, 6(1): 3-73.",
        "[12] Hyndman R J, Koehler A B. Another look at measures of forecast accuracy[J]. "
        "International Journal of Forecasting, 2006, 22(4): 679-688. "
        "DOI: 10.1016/j.ijforecast.2006.03.001.",
        "[13] 周志华. 机器学习[M]. 北京: 清华大学出版社, 2016.",
        "[14] McKinney W. Python for Data Analysis: Data Wrangling with pandas, NumPy, and "
        "Jupyter[M]. 3rd ed. Sebastopol: O'Reilly Media, 2022.",
        "[15] Henderson B D. The Product Portfolio[M]. Boston: Boston Consulting Group, 1970.",
        "[16] Streamlit. Streamlit Documentation[EB/OL]. (2026-10-30). https://docs.streamlit.io.",
        "[17] Plotly Technologies Inc. Plotly Python Open Source Graphing Library[EB/OL]. "
        "(2026-10-30). https://plotly.com/python/.",
    ]
    for ref in refs:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
        pf.line_spacing = 1.3
        pf.space_after = Pt(3)
        pf.left_indent = Cm(0.74)
        pf.first_line_indent = Cm(-0.74)
        r = p.add_run(ref)
        set_run(r, cn=CN_FONT, size=10.5)


def appendix(doc):
    h1(doc, "附录")
    h2(doc, "A  核心代码片段")
    body_para(doc,
              "以下代码摘自仓库 scripts/01_load.py、02_clean.py、03_analysis.py 与 05_dashboard.py，"
              "仅保留关键逻辑，完整代码见公开仓库；核心字段说明见表 2-2。")
    code_block(doc,
               '''# 1) 官方文件断点续传（01_load.py）
def download(url, dest, retries=3):
    remote = head_size(url)
    if dest.exists() and dest.stat().st_size > 1024:
        if remote is None or dest.stat().st_size == remote:
            return "skip"
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, retries + 1):
        have = tmp.stat().st_size if tmp.exists() else 0
        headers = dict(UA)
        if have:
            headers["Range"] = f"bytes={have}-"
        with urlopen(Request(url, headers=headers), timeout=120) as resp, \\
                open(tmp, "ab") as fh:
            while chunk := resp.read(1 << 20):
                fh.write(chunk)
        tmp.replace(dest)
        return "download"''')
    code_block(doc,
               '''# 2) 流式清洗的保留规则（02_clean.py）
bad_dur  = ~df["duration_min"].between(1, 240)
bad_dist = ~df["distance_mi"].between(0.01, 100)
bad_amt  = (df["fare"] < 0) | (df["total"] < 0)
bad_zone = ~(df["PULocationID"].isin(zone_ids) &
             df["DOLocationID"].isin(zone_ids))
keep = ~(bad_dur | bad_dist | bad_amt | bad_zone)
df = df.loc[keep].copy()
df["speed_mph"] = df["distance_mi"] / (df["duration_min"] / 60.0)''')
    code_block(doc,
               '''# 3) SARIMAX 验证集选型（03_analysis.py）
for p, d, q, P, Q in cands:
    m = SARIMAX(val_train, exog=exog.loc[val_train.index],
                order=(p, d, q), seasonal_order=(P, 0, Q, 7),
                enforce_stationarity=False)
    f = m.fit(disp=False, maxiter=120)
    vp = f.get_forecast(steps=len(val_test),
                        exog=exog.loc[val_test.index]).predicted_mean
    vm = mape(val_test.values, vp)
    if chosen is None or vm < chosen[0]:
        chosen = (vm, (p, d, q), (P, 0, Q, 7))''')
    code_block(doc,
               '''# 4) 区域聚类与轮廓系数（03_analysis.py）
Z = StandardScaler().fit_transform(features)
for k in (4, 5, 6):
    km = KMeans(n_clusters=k, n_init=20, random_state=SEED).fit(Z)
    scores[k] = silhouette_score(Z, km.labels_)
k_best = max(scores, key=scores.get)
pca = PCA(n_components=2, random_state=SEED).fit_transform(Z)''')
    code_block(doc,
               '''# 5) 大屏筛选与联动（05_dashboard.py）
mask = ((dzp["date"] >= pd.Timestamp(d0)) & (dzp["date"] <= pd.Timestamp(d1))
        & dzp["行政区"].isin(bor_sel) & dzp["支付方式"].isin(pay_sel))
if air_sel != "全部":
    mask &= dzp["机场"] == air_sel
df = dzp.loc[mask]
trips = float(df["trips"].sum())
revenue = float(df["revenue"].sum())
card = float(df.loc[df["支付方式"] == "信用卡", "trips"].sum())''')

    h2(doc, "B  Gitee/github 仓库链接与目录结构")
    body_para(doc,
              "仓库地址：https://github.com/SomniaF/shujufenxi。"
              "仓库包含脚本、图表、聚合表、论文与合规声明；原始数据与清洗后数据因体积较大不随仓库"
              "分发，运行 run_all.py --download 可自动重建。")
    code_block(doc,
               '''repo/
├── data/raw/                 # 12 个月度 Parquet、区域表、边界 SHP
├── data/clean/               # trips_sample.parquet（120 万行）
├── scripts/
│   ├── config.py             # 路径、配色、中文映射
│   ├── 01_load.py            # 官方下载 + 审计
│   ├── 02_clean.py           # 流式清洗、派生、聚合
│   ├── 03_analysis.py        # 六组模型
│   ├── 04_visuals.py         # 33 张静态图
│   ├── 05_dashboard.py       # Streamlit 大屏
│   ├── 06_snapshot.py        # Selenium 截图（仅本地）
│   ├── 07_build_paper.py     # 论文生成
│   └── 08_compliance.py      # 合规声明
├── outputs/figures/          # fig01–fig33
├── outputs/tables/           # 聚合表、模型指标 JSON
├── outputs/dashboard/        # 大屏截图
├── docs/                     # 论文、合规声明
├── requirements.txt
├── run_all.py
└── README.md''')
    body_para(doc,
              "数据文件分为三层：data/raw 保存 12 个月度 Parquet、区域查询表与分区边界 Shapefile；"
              "data/clean 保存 120 万行分层样本 trips_sample.parquet，用于分布图与模型；outputs/tables"
              " 保存日、月、分区、OD、支付、小费等聚合表与模型指标 JSON。")

    h2(doc, "C  图表索引")
    body_para(doc,
              "正文共 33 幅图：图 5-1 至图 5-30 为静态图，位于 outputs/figures/；图 5-31 至图 5-33 "
              "为大屏截图，位于 outputs/dashboard/。编号与表 C-1 一一对应。")
    items = [
        ("图 5-1", "月度行程量"),
        ("图 5-2", "日行程量与移动平均"),
        ("图 5-3", "星期×小时热力图"),
        ("图 5-4", "工作日与周末对比"),
        ("图 5-5", "月度收入构成"),
        ("图 5-6", "支付方式结构"),
        ("图 5-7", "行程时长分布"),
        ("图 5-8", "行程距离分布"),
        ("图 5-9", "速度分布"),
        ("图 5-10", "小费率分布"),
        ("图 5-11", "小费率时段曲线"),
        ("图 5-12", "小费率热力图"),
        ("图 5-13", "区域收入帕累托"),
        ("图 5-14", "区域收入气泡地图"),
        ("图 5-15", "行政区收入构成"),
        ("图 5-16", "机场与非机场对比"),
        ("图 5-17", "SARIMAX 拟合与预测"),
        ("图 5-18", "12 月预测误差"),
        ("图 5-19", "12 月实际与预测"),
        ("图 5-20", "区域聚类 PCA"),
        ("图 5-21", "聚类雷达图"),
        ("图 5-22", "聚类时段曲线"),
        ("图 5-23", "聚类空间分布"),
        ("图 5-24", "小费模型 ROC"),
        ("图 5-25", "小费特征重要性"),
        ("图 5-26", "区域 ABC 分层"),
        ("图 5-27", "区域机会矩阵"),
        ("图 5-28", "STL 异常检测"),
        ("图 5-29", "Top 20 OD 走廊"),
        ("图 5-30", "Top 20 OD 行程量"),
        ("图 5-31", "大屏首屏"),
        ("图 5-32", "大屏全页"),
        ("图 5-33", "站点下钻"),
    ]
    per_col = 11
    headers = ["图号 / 图名"] * 3
    rows = []
    for i in range(per_col):
        row = []
        for g in range(3):
            k = g * per_col + i
            row.append(f"{items[k][0]}  {items[k][1]}" if k < len(items) else "")
        rows.append(row)
    table(doc, "表 C-1  图表索引（图 5-1—图 5-33）", headers, rows,
          font=8.2, widths=[4.83, 4.83, 4.83])


def grading_table(doc):
    headers = ["评分维度", "评分要点（子项及分值）", "得分"]
    rows = [
        ["1. 数据获取合规性与清洗质量（15分）",
         "① 来源合规、白名单方式、合规声明完整（5）；② 数据量达标、抽样方法与随机种子说明（4）；"
         "③ 清洗完整、异常/缺失/重复处理、多表对齐（4）；④ 可导出 CSV/JSON/SQLite 复用（2）", ""],
        ["2. 商业分析模型应用深度（20分）",
         "① 模型≥3种、选型与场景匹配（6）；② 计算正确、参数与阈值有业务依据（6）；"
         "③ 预测类含置信区间与回测误差（4）；④ 结论与模型一一对应（4）", ""],
        ["3. 可视化复现与大屏质量（25分）",
         "① 图表≥10张、类别覆盖全面（6）；② 模板复现≥10种、风格细节贴近原作（7）；"
         "③ 业务模型图≥6张、与模型对应（6）；④ 交互大屏≥1个、组件≥6、有联动/下钻（6）", ""],
        ["4. 代码规范性与文档完整性（10分）",
         "① 目录结构清晰、注释充分（3）；② README 详实、依赖明确（3）；"
         "③ 可一键复现（2）；④ 图表命名与索引规范（2）", ""],
        ["5. 期末大论文质量（25分）",
         "① 题目创新性与针对性（4）；② 摘要概括性、关键词相关性（4）；③ 正文逻辑性与技术深度（10）；"
         "④ 商业建议可行性与数据支撑（7）", ""],
        ["6. 创新性与商业洞察深度（5分）",
         "① 引入新工具/新方法（2）；② 提出有效商业建议（2）；③ 体现批判性思维（1）", ""],
        ["总 分", "（各维度得分相加）", ""],
    ]
    t = doc.add_table(rows=len(rows) + 1, cols=3)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    widths = [3.24, 10.50, 1.49]
    tblPr = t._tbl.tblPr
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.insert_element_before(
            tblW, "w:jc", "w:tblCellSpacing", "w:tblInd", "w:tblBorders",
            "w:shd", "w:tblLayout", "w:tblCellMar", "w:tblLook")
    tblW.set(qn("w:type"), "pct")
    tblW.set(qn("w:w"), "5000")
    for i, w in enumerate(widths):
        t.columns[i].width = Cm(w)
        for row in t.rows:
            row.cells[i].width = Cm(w)
    for i, row in enumerate(t.rows):
        row.height = Cm(0.5168) if i < len(t.rows) - 1 else Cm(0.1129)

    for j, text in enumerate(headers):
        cell = t.cell(0, j)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing = 1.5
        p.add_run(text)
        set_run(p.runs[-1], cn=CN_FONT, size=9, bold=True, color=(0, 0, 0))

    for i, row in enumerate(rows, start=1):
        last = i == len(rows)
        for j, text in enumerate(row):
            cell = t.cell(i, j)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (last or j == 2) else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.5
            p.add_run(text)
            set_run(p.runs[-1], cn=CN_FONT, size=10 if last else 9,
                    bold=last, color=(0, 0, 0))


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = EN_FONT
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), CN_FONT)
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(0)

    cover(doc)
    front_matter(doc)
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    set_page(sec)
    clear_numbering(sec)
    add_header_footer(sec)

    chapter1(doc)
    chapter2(doc)
    chapter3(doc)
    chapter4(doc)
    chapter5(doc)
    chapter6(doc)
    chapter7(doc)
    references(doc)
    appendix(doc)

    doc.save(OUT)
    cjk = sum(1 for ch in ABSTRACT if "\u4e00" <= ch <= "\u9fff")
    body_chars = sum(len(p.text) for p in doc.paragraphs)
    print(f"[输出] {OUT}")
    print(f"[检查] 摘要汉字数={cjk}，关键词={KEYWORDS}")
    print(f"[检查] 段落总字符数={body_chars}，图片数={len(doc.inline_shapes)}，表格数={len(doc.tables)}")


if __name__ == "__main__":
    sys.exit(main())
