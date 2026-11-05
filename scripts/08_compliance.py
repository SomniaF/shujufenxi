# -*- coding: utf-8 -*-
"""生成《数据来源与使用合规声明》Word 文档（NYC TLC 2024）。"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "数据来源与使用合规声明.docx"

CN_FONT = "宋体"
HEI = "黑体"
KAI = "楷体"
EN_FONT = "Times New Roman"

SOURCE_PAGE = "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page"
TLC_BASE = "https://d37ci6vzurychx.cloudfront.net"

FILES = [
    ("yellow_tripdata_2024-01.parquet", 2964624, 49961641, "c4d59da7bbc8abaeeeb1727947ee93d9891a71acb42854bd80db1571b2030510"),
    ("yellow_tripdata_2024-02.parquet", 3007526, 50349284, "c76c43c18c6c6664080dd920baab4928988d5786a6b65980792ca7cd796f9f20"),
    ("yellow_tripdata_2024-03.parquet", 3582628, 60078280, "2d4cdc8fb96726cdd3803b13b02d2e61e71d45720aff0ebc693a8bdd1f249823"),
    ("yellow_tripdata_2024-04.parquet", 3514289, 59133625, "ce37f736c7cf9e92164c850ef2b502a8f7bb590fc1804b6edbcb80293da01b89"),
    ("yellow_tripdata_2024-05.parquet", 3723833, 62553128, "1974230be2b5a3ea92e47b5eb77f32dbf1de896d81ad8df4ab6faba52749ad23"),
    ("yellow_tripdata_2024-06.parquet", 3539193, 59859922, "677cf14c8347f745b583f012fbdba072334c6c4efa17bfd6a64369f2ba30329c"),
    ("yellow_tripdata_2024-07.parquet", 3076903, 52299432, "af12d6b04daeb78550799ae99933d495b27d715b6dbb0fad9bb750a4537d3070"),
    ("yellow_tripdata_2024-08.parquet", 2979183, 51067350, "7315643dd16bafc03e27d9903edbfd35404c2550a695d0da0a3e73852d940cfb"),
    ("yellow_tripdata_2024-09.parquet", 3633030, 61170186, "2f42e4a383a6635de803001462848d0aee2b47f6ce899126805d2d05361fb843"),
    ("yellow_tripdata_2024-10.parquet", 3833771, 64346071, "d19fe05aa0b259af24eb47051735293287f1e6dc263ba04030ec1ab4c6ec2650"),
    ("yellow_tripdata_2024-11.parquet", 3646369, 60658709, "5ef321876de5007a7c147a347389133fc94fd7ac28f82eb1d57d8f2cf05cfd3b"),
    ("yellow_tripdata_2024-12.parquet", 3668371, 61524085, "41ebf7db80bebde60c58e5143c14cdf38ad04a0f3e3ff44215b3e240d55f6c78"),
]
AUX = [
    ("taxi_zone_lookup.csv", 12331, "1a99e105092230f8620f301edcca7f80d3080642ff404d28ed957d3fa222c8ed"),
    ("taxi_zones.zip", 1022574, "f6d711917bb4340f8f644d5366c51665489eb2d426dd1a4a55677721ae5adf17"),
]


def set_run(run, cn=CN_FONT, size=12, bold=False, color=None, en=EN_FONT):
    run.font.name = en
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), cn)
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def set_page(section):
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.75)
    section.right_margin = Cm(2.5)
    section.header_distance = Cm(1.5)
    section.footer_distance = Cm(1.5)


def add_header_footer(section):
    hp = section.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    hr = hp.add_run("商业数据分析")
    set_run(hr, size=9)
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
    set_run(run, size=9)
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


def body_para(doc, text, indent=True, size=12, space_after=6, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
              bold=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = align
    pf.line_spacing = 1.5
    pf.space_after = Pt(space_after)
    if indent:
        pf.first_line_indent = Pt(size * 2)
    r = p.add_run(text)
    set_run(r, size=size, bold=bold)
    return p


def h1(doc, text):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(12)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.5
    pf.keep_with_next = True
    r = p.add_run(text)
    set_run(r, cn=HEI, size=13, bold=True)
    return p


def shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def table(doc, headers, rows, font=9.0, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0]
    trPr = hdr._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trPr.append(th)
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.vertical_alignment = 1
        shade(cell, "1F4E79")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(str(h))
        set_run(r, cn=HEI, size=font, bold=True, color=(0xFF, 0xFF, 0xFF))
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cell = cells[i]
            cell.vertical_alignment = 1
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_before = Pt(1.5)
            p.paragraph_format.space_after = Pt(1.5)
            r = p.add_run(str(v))
            set_run(r, size=font)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Cm(w)
    gap = doc.add_paragraph()
    gap.paragraph_format.space_after = Pt(2)
    gap.paragraph_format.line_spacing = 1.0
    return t


def main():
    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = EN_FONT
    normal.font.size = Pt(12)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), CN_FONT)
    sec = doc.sections[0]
    set_page(sec)
    add_header_footer(sec)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(24)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run("数据来源与使用合规声明")
    set_run(r, cn=HEI, size=20, bold=True)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(18)
    r = p.add_run("《商业数据分析》期末大作业")
    set_run(r, cn=KAI, size=14)

    table(doc, ["项目", "内容"], [
        ["数据集", "NYC TLC Yellow Taxi Trip Records 2024"],
        ["学院 / 专业", "数据科学学院 / 数据科学与大数据技术"],
        ["作者 / 学号", "＿＿＿＿＿＿＿＿ / ＿＿＿＿＿＿＿＿"],
        ["完成日期", "2026年11月1日"],
    ], font=10.5, widths=[4.0, 11.6])

    h1(doc, "一、数据集基本信息")
    table(doc, ["条目", "说明"], [
        ["数据集名称", "New York City TLC Yellow Taxi Trip Records（2024 年 1—12 月）"],
        ["数据提供方", "New York City Taxi and Limousine Commission（纽约市出租车与豪华轿车委员会，TLC）"],
        ["数据页面", SOURCE_PAGE],
        ["下载域", TLC_BASE + "（TLC 官方 CloudFront 托管）"],
        ["获取方式", "Python urllib 通过 HTTPS 直接下载官方 Parquet / CSV / ZIP 文件，支持断点续传"],
        ["获取日期", "2026年10月30日"],
        ["许可与条款", "纽约市政府公开发布的匿名行程数据；按 TLC 数据页说明与 NYC Open Data 使用条款使用，数据按原样提供、不作准确性担保"],
        ["分析窗口", "2024-01-01 至 2024-12-31（以乘客上车时间为准，时区为 America/New_York）"],
        ["数据规模", "12 个月度 Parquet，合计 41,169,720 行、693,001,713 字节（660.9 MiB）"],
        ["辅助文件", "taxi_zone_lookup.csv（265 个区域名称与行政区）、taxi_zones.zip（区域边界 Shapefile）"],
    ], font=9.0, widths=[3.4, 12.2])
    body_para(doc,
              "上述数据为 TLC 按月度公开发布的黄色出租车行程记录，字段包括上下车时间、乘客数、"
              "行程距离、费率代码、上下车区域编号、支付方式、车费、小费、路桥费、拥堵费与总金额。"
              "区域编号需与 taxi_zone_lookup.csv 关联后才能还原为地名，边界文件用于绘制分区地图。")

    h1(doc, "二、获取方式与合规性")
    body_para(doc,
              "本项目数据全部来自纽约市 TLC 官方数据页所列的下载地址，属于课程允许的“官方网站文件下载”"
              "方式。下载前核对数据页的字段说明与使用条款，下载后逐个计算 SHA-256 并与审计记录比对，"
              "全过程由 scripts/01_load.py 完成，可重复执行。")
    body_para(doc,
              "（1）官方渠道。12 个月度文件均从 TLC 官方 CloudFront 域名的 /trip-data/ 路径下载，"
              "区域查询表与边界文件从 /misc/ 路径下载；未使用第三方镜像、网盘转存、论坛附件或来源不明的"
              "数据副本，也未使用 Kaggle 等二次分发页面。")
    body_para(doc,
              "（2）技术实现。脚本使用 Python 标准库 urllib 发起 HTTPS 请求，先以 HEAD 获取文件长度，"
              "再以 1 MiB 分块写入临时文件，支持 Range 断点续传；下载完成后用 pyarrow 读取 Parquet 元数据，"
              "记录行数、列名、字节数与 SHA-256，生成 outputs/tables/raw_audit.json。整个过程只访问上述"
              "官方文件地址，不解析网页、不执行页面脚本。")
    body_para(doc,
              "（3）未使用爬虫。本项目未使用 Scrapy、requests + HTML 解析、Playwright 等网页抓取技术，"
              "未模拟登录、未绕过验证码、robots 协议、访问频率限制或付费墙，也未对 TLC 网站发起高频请求。"
              "项目中的 Selenium 仅用于对本地运行的 Streamlit 大屏（localhost:8501）自动截图，供论文插图使用；"
              "它不访问外部网站，也不采集任何数据。")
    body_para(doc,
              "（4）数据性质。TLC 行程数据是纽约市政府主动公开的匿名运营记录，用于监管、研究与分析。"
              "数据页明确说明数据按原样提供，TLC 不对其准确性、完整性或及时性作担保；本文在使用中对明显"
              "异常值做了清洗，并在论文中披露清洗规则与保留率，不把原始数据直接当作“真值”。")

    h1(doc, "三、许可与使用范围")
    body_para(doc,
              "本项目按 NYC Open Data 使用条款与 TLC 数据页说明使用数据：①仅用于嘉兴大学《商业数据分析》"
              "课程期末作业与相关课堂展示，不用于任何商业目的；②在论文、图表与仓库中标注数据来源为 "
              "NYC TLC；③不声称对原始数据拥有版权，也不对数据作超出其发布口径的再保证。")
    body_para(doc,
              "原始 Parquet、区域边界与查询表合计约 661 MiB，体积较大且属于政府原始发布物，因此不提交到"
              "公开仓库；仓库通过 .gitignore 排除 data/raw 与 data/clean，仅提交脚本、聚合表、图表与文档。"
              "120 万行分层样本与聚合中间表不随仓库分发，运行 python run_all.py --download 即可从上述"
              "官方地址重建全部原始数据、清洗结果、图表与大屏。")
    body_para(doc,
              "若课程要求、NYC Open Data 使用条款或 TLC 数据页说明之间存在冲突，以更严格者为准；"
              "如数据提供方提出异议，将立即停止使用并删除相关数据副本。")

    h1(doc, "四、文件清单与完整性校验")
    body_para(doc,
              "下表列出 12 个月度文件的规模与 SHA-256。校验值由 scripts/01_load.py 在下载后计算，"
              "与 outputs/tables/raw_audit.json 中记录一致；重新下载后可用同一脚本复核。", space_after=3)
    rows = [(name, f"{rows:,}", f"{size/1048576:.1f}", sha) for name, rows, size, sha in FILES]
    rows += [(name, "—", f"{size/1048576:.2f}", sha) for name, size, sha in AUX]
    table(doc, ["文件", "行数", "MiB", "SHA-256"], rows, font=6.8,
          widths=[4.3, 2.0, 1.3, 8.0])
    body_para(doc,
              "12 个行程文件合计 41,169,720 行；区域查询表 265 行（含未知区域与市外区域各 1 行），"
              "边界文件包含 263 个分区面。文件行数与 TLC 数据页的月度规模一致，未发现截断或重复下载。",
              space_after=6)

    h1(doc, "五、数据内容与字段使用")
    body_para(doc,
              "本文使用的主要字段包括：tpep_pickup_datetime / tpep_dropoff_datetime（上下车时间）、"
              "passenger_count（乘客数）、trip_distance（里程）、RatecodeID（费率代码）、"
              "PULocationID / DOLocationID（上下车分区）、payment_type（支付方式）、fare_amount（车费）、"
              "tip_amount（小费）、tolls_amount（路桥费）、congestion_surcharge（拥堵费）、"
              "Airport_fee（机场费）与 total_amount（总金额）。")
    body_para(doc,
              "由上述字段派生出行程时长、平均速度、小时、星期、是否周末、是否高峰、时段、小费率、"
              "是否慷慨小费、是否机场相关行程、上车/下车行政区等分析变量。金额单位均为美元；"
              "小费率仅在信用卡支付且车费大于 0 时计算，现金支付的小费不可观测，相关结论不外推到现金行程。"
              "机场相关行程的定义为：费率代码属于 JFK（2）或 Newark（3），或上下车分区属于 1、132、138。")

    h1(doc, "六、隐私与伦理")
    body_para(doc,
              "TLC 行程数据不含乘客姓名、电话、邮箱、身份证号、银行卡号或司机身份信息，也不含精确门牌"
              "地址；位置信息仅到出租车分区（zone）级别，时间为分钟级。数据由 TLC 在发布前做匿名化处理，"
              "本文未尝试与任何外部数据关联，也未进行个体识别或再识别。")
    body_para(doc,
              "本文的分析单位是行程、分区、小时与日期，所有结论以聚合口径呈现；涉及区域差异的表述仅用于"
              "运营建议，不对任何乘客、司机、社区或行政区作贬损性评价。论文中的地图只展示分区边界与聚合"
              "指标，不展示单笔行程的起讫点轨迹。")

    h1(doc, "七、数据处理与留存")
    body_para(doc,
              "原始数据共 41,169,720 行。清洗规则为：①仅保留上车时间在 2024 年内的记录；②行程时长限定"
              "1—240 分钟，里程限定 0.01—100 英里，车费与总金额非负；③上下车分区须在 TLC 1—263 号"
              "区域内；④乘客数缺失不删除，保留并在分析中按可用样本处理；⑤小费率仅对信用卡且车费大于 0 "
              "的行程计算。清洗后保留 39,192,643 行，保留率 95.20%。")
    body_para(doc,
              "被剔除的记录为：时长异常 524,922 行、里程异常 777,918 行、金额为负 733,884 行、分区异常 "
              "425,655 行、跨年记录 56 行（同一记录可能触发多条规则，故各项之和大于剔除总数）。"
              "按“上下车时间 + 上下车分区 + 总金额”识别的重复键共 9 行；TLC 数据不含行程唯一编号，"
              "无法做严格去重，该计数仅用于质量披露。乘客数、费率代码、拥堵费与机场费四个字段各有 "
              "4,091,232 行为空，本文未对其做插补，而是在相应分析中排除或单独标注。")
    body_para(doc,
              "为兼顾可视化与建模，本文另抽取 120 万行分层样本（每月 10 万行，随机种子为 42 加月份序号），"
              "仅用于分布图、散点图与小费模型；总量、收入、分区排名与预测均使用全量聚合表。原始数据与"
              "清洗后的明细仅保存在本地，不进入版本库、不公开分享；仓库只保留聚合表、图表与脚本。"
              "课程结束后可按教师要求删除本地原始数据副本。")

    h1(doc, "八、声明")
    body_para(doc,
              "本人声明：上述数据获取、使用与共享行为真实、合规；数据来自 NYC TLC 官方发布地址，"
              "未使用网页爬虫或任何规避访问控制的手段；已阅读并遵守 TLC 数据页说明与 NYC Open Data "
              "使用条款；论文中的分析结果由本人基于上述数据完成，所有数值均与 outputs/tables 下的结果表"
              "核对。通用 AI 编程助手仅用于查询个别 API 用法、排查运行错误与语句润色，不参与数据获取、"
              "清洗口径、模型设定与结论形成；AI 使用情况已在论文第 7.3 节披露。")
    body_para(doc, "作者签名：＿＿＿＿＿＿＿＿＿＿　　　　日期：2026 年 11 月 1 日", indent=False)

    doc.save(OUT)
    print("[输出]", OUT)


if __name__ == "__main__":
    main()
