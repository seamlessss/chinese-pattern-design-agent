from __future__ import annotations
import json
import os
from pathlib import Path
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from src.agent import DesignAgent
from src.config import load_config, project_path
from src.data import audit_patterns, load_patterns
from src.generation import BailianImageProvider, GenerationError, GenerationResult, OpenAIImageProvider, bailian_api_key, build_pattern_prompt, generate_programmatic_svg, image_api_key, save_generation
from src.ontology import PatternGraph
from src.retrieval import TextRetriever
from src.vision import analyze_features, extract_features, feature_frame, visual_neighbors

st.set_page_config(page_title="纹样知策 · 设计工作台", page_icon="纹", layout="wide", initial_sidebar_state="expanded")
DESIGN_CSS = """
<style>
:root { --paper:#F4F1E9; --surface:#FFFEFB; --ink:#292923; --muted:#706F68; --line:#D9D5CB; --accent:#9E4037; --accent-soft:#F4E8E5; --shadow:0 8px 24px rgba(38,35,29,.045); }
html,body,[class*="css"] {font-family:"Noto Sans CJK SC","Microsoft YaHei UI","PingFang SC",sans-serif;color:var(--ink)}
.stApp {background:var(--paper)} header[data-testid="stHeader"]{background:rgba(244,241,233,.94)}
.stApp,.stApp p,.stApp li,.stApp span,.stApp label,.stApp div[data-testid="stMarkdownContainer"]{color:var(--ink)}
.block-container{max-width:1380px;padding:2.1rem 2.7rem 4rem}
h1,h2,h3{font-family:"Noto Serif CJK SC","Songti SC","SimSun",serif;color:var(--ink);letter-spacing:0}
.stApp h1,.stApp h2,.stApp h3,[data-testid="stHeadingWithActionElements"]{color:var(--ink)!important}
h1{font-size:2.1rem;line-height:1.35;font-weight:650;margin:0 0 .55rem}
h2{font-size:1.38rem;line-height:1.5;font-weight:620;margin:1.45rem 0 .55rem}
h3{font-size:1.04rem;line-height:1.5;font-weight:620}
p,li,label,[data-testid="stMarkdownContainer"]{line-height:1.7}
small,.stCaption,[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:var(--muted)!important}
.eyebrow{color:var(--accent);font-size:.72rem;font-weight:700;letter-spacing:.16em;margin-bottom:.55rem;text-transform:uppercase}
.lede{max-width:780px;font-size:1rem;color:#55564F;line-height:1.85}
.surface-note{border-left:3px solid var(--accent);background:var(--surface);padding:.85rem 1rem;color:#55564F;border-radius:0 5px 5px 0}
.result-score{color:var(--accent);font-weight:750;font-variant-numeric:tabular-nums}
.source-line{color:var(--muted);font-size:.79rem;line-height:1.6}
.image-label{display:inline-block;color:var(--accent);background:var(--accent-soft);border:1px solid #E7CFCB;padding:.17rem .5rem;border-radius:3px;font-size:.74rem;font-weight:700}
div[data-testid="stMetric"]{background:var(--surface);border:1px solid var(--line);border-radius:5px;padding:.85rem 1rem;box-shadow:var(--shadow)}
div[data-testid="stMetricLabel"]{color:var(--muted);font-size:.78rem}
div[data-testid="stMetricValue"]{color:var(--ink);font-size:1.5rem;font-variant-numeric:tabular-nums}
div[data-testid="stVerticalBlockBorderWrapper"]{background:var(--surface);border-color:var(--line);border-radius:5px;box-shadow:var(--shadow)}
[data-testid="stSidebar"]{background:#EAE6DD;border-right:1px solid var(--line)}
[data-testid="stSidebar"] .block-container{padding:1.35rem 1rem}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,[data-testid="stSidebar"] label{color:var(--ink)!important}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{color:#66655E!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label{padding:.18rem .2rem;font-weight:560}
[data-testid="stSidebar"] [role="radiogroup"]{gap:.28rem}
[data-testid="stSidebar"] [data-testid="stRadio"] p{color:var(--ink)!important}
.stButton>button,.stDownloadButton>button,.stLinkButton>a{border-radius:4px!important;min-height:2.55rem;font-weight:650;transition:all .15s ease}
.stButton>button:not([kind="primary"]),.stDownloadButton>button,.stLinkButton>a{border-color:var(--line);background:var(--surface);color:var(--ink)}
.stButton>button[kind="primary"]{background:var(--accent);border-color:var(--accent);color:#fff}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--accent);color:var(--accent)}
[data-baseweb="input"]>div,[data-baseweb="textarea"]>div,[data-baseweb="select"]>div{border-radius:4px!important;border-color:#C9C5BB!important;background:var(--surface)!important}
[data-baseweb="input"] input,[data-baseweb="textarea"] textarea,[data-baseweb="select"] input{color:var(--ink)!important;-webkit-text-fill-color:var(--ink)!important;caret-color:var(--accent)!important}
[data-baseweb="input"] input::placeholder,[data-baseweb="textarea"] textarea::placeholder{color:#797870!important;opacity:1!important;-webkit-text-fill-color:#797870!important}
[data-baseweb="select"] span,[data-baseweb="popover"] span,[role="option"]{color:var(--ink)!important}
[data-testid="stWidgetLabel"] p,[data-testid="stWidgetLabel"] label,[data-testid="stSlider"] p{color:var(--ink)!important;font-weight:600}
[data-testid="stFileUploader"] section{background:#F9F7F1!important;border:1px dashed #A8A398!important}
[data-testid="stFileUploader"] section span,[data-testid="stFileUploader"] section small,[data-testid="stFileUploader"] section div{color:var(--ink)!important}
[data-testid="stFileUploaderDropzoneInstructions"] span{color:var(--ink)!important}
[data-testid="stFileUploaderDropzoneInstructions"] small{color:var(--muted)!important}
[data-testid="stFileUploader"] button{background:var(--surface)!important;color:var(--ink)!important;border-color:#AAA59A!important}
[data-testid="stSlider"] [role="slider"]{background:var(--accent)!important}
[data-testid="stSlider"] [data-testid="stThumbValue"]{color:var(--accent)!important}
[data-testid="stProgress"] p{color:var(--ink)!important}
[aria-disabled="true"],button:disabled{color:#6E6D66!important;opacity:.72!important}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:5px;overflow:hidden}
[data-testid="stAlert"]{border-radius:4px;border-left-width:3px}
[data-testid="stImage"] img{border-radius:4px;object-fit:cover}
[data-testid="stPlotlyChart"]{border:1px solid var(--line);border-radius:5px;background:var(--surface);padding:.35rem}
hr{border-color:var(--line)}
@media(max-width:850px){.block-container{padding:1.3rem 1rem 3rem}h1{font-size:1.7rem}}
</style>
"""
st.markdown(DESIGN_CSS, unsafe_allow_html=True)
PAGES=["首页","纹样图鉴与详情","知识图谱","视觉分析","设计辅助智能体","AI 纹样创作室","数据与方法"]
if "navigation" not in st.session_state: st.session_state.navigation="首页"
if "studio_reference_id" not in st.session_state: st.session_state.studio_reference_id=""

@st.cache_data(show_spinner=False)
def data(): return load_patterns()

@st.cache_resource(show_spinner=False)
def services(_signature: int):
    frame=data(); graph=PatternGraph(frame); retriever=TextRetriever(frame)
    index,vectors=feature_frame(frame,project_path(load_config()["paths"]["feature_npz"]))
    return graph,retriever,index,vectors

df=data()
graph,retriever,vision_index,vision_vectors=services(len(df))
cfg=load_config()
openai_key=image_api_key(secrets=st.secrets)
bailian_key=bailian_api_key(secrets=st.secrets)

def intro(kicker,title,description):
    st.markdown(f"<div class='eyebrow'>{kicker}</div>",unsafe_allow_html=True)
    st.title(title)
    st.markdown(f"<div class='lede'>{description}</div>",unsafe_allow_html=True)

def display_source_name(value):
    """Keep internal source IDs stable while presenting a natural Chinese label."""
    name=str(value or "").strip()
    if name.lower() in {"wényàng", "wenyang"} or "wényàng" in name.lower():
        return "《中国传统纹样图鉴》"
    return name or "未知来源"

def show_image(row):
    path=str(row.get("image_path",""))
    if path and Path(path).is_file():
        st.image(path,use_container_width=True)
        st.markdown("<span class='image-label'>数据集原图 · 原创再设计</span>",unsafe_allow_html=True)
    else: st.info("当前记录没有本地原图。")

def source_caption(row):
    st.markdown(f"<div class='source-line'>来源：{display_source_name(row.get('source_name'))} · {row.get('license','许可未知')}</div>",unsafe_allow_html=True)

def set_navigation(target): st.session_state.navigation=target

def set_creation_reference(row):
    st.session_state.studio_reference_id=row["pattern_id"]
    st.session_state.navigation="AI 纹样创作室"

def pattern_detail(row):
    left,right=st.columns([1,1.25],gap="large")
    with left: show_image(row)
    with right:
        st.markdown(f"<div class='eyebrow'>{row.get('category','纹样资料')}</div>",unsafe_allow_html=True)
        st.subheader(row["name"])
        if row.get("name_en"): st.caption(row["name_en"])
        st.write(row.get("summary","") or "暂无摘要")
        fields=[("文化寓意",row.get("cultural_meaning","")),("适用载体",row.get("application_context","")),("历史时期",row.get("historical_period","")),("视觉特征","、".join(row.get("visual_keywords",[]) or []))]
        for label,value in fields:
            with st.container(border=True):
                st.caption(label); st.write(value or "未知 / 来源未提供")
        st.info("文化信息为数据集自身描述，尚无外部独立核验。")
        source_caption(row); st.link_button("打开上游来源",row["source_url"])
        st.button("以此纹样进入创作室",on_click=set_creation_reference,args=(row,),key=f"detail-create-{row['pattern_id']}")

def home():
    left,right=st.columns([1.5,1],gap="large",vertical_alignment="center")
    with left:
        st.markdown("<div class='eyebrow'>东方纹样 · 数字设计工作台</div>",unsafe_allow_html=True)
        st.title("纹样知策")
        st.subheader("从纹样资料，走向设计探索。")
        st.markdown("<div class='lede'>以可追溯的传统纹样资料为起点，结合知识图谱、视觉检索与生成式创作，建立一条看得见来源、分得清证据的设计路径。</div>",unsafe_allow_html=True)
        st.write("")
        st.button("开始一次设计探索",type="primary",on_click=set_navigation,args=("设计辅助智能体",))
    with right:
        if len(df): show_image(df.iloc[0]); st.caption("缠枝莲纹 · 《中国传统纹样图鉴》卡片图")
    audit=audit_patterns(df); stats=graph.stats()
    values=[audit["records"],audit["available_images"],sum(stats["relation_types"].values()),len(retriever.documents)]
    metrics=st.columns(4)
    for col,label,value in zip(metrics,["纹样记录","本地图片","图谱关系","文本资料片段"],values): col.metric(label,value)
    st.subheader("工作台入口")
    entries=[("纹样图鉴与详情","纹样图鉴","检索原始记录与来源"),("知识图谱","知识图谱与问答","浏览实体关系和证据片段"),("视觉分析","视觉分析","查看真实颜色特征与聚类"),("AI 纹样创作室","AI 纹样创作室","生成新图案或程序化纹样")]
    for col,(target,label,desc) in zip(st.columns(4),entries):
        with col:
            with st.container(border=True):
                st.markdown(f"**{label}**"); st.caption(desc)
                st.button("进入",key=f"home-{target}",on_click=set_navigation,args=(target,))

def gallery():
    intro("COLLECTION","纹样图鉴","检索有来源记录。图片、文化描述与历史信息分别标注，未知内容不会补写。")
    with st.container(border=True):
        a,b,c=st.columns([1.4,1,1])
        query=a.text_input("关键词",placeholder="名称、寓意、摘要或视觉词",key="gallery_q")
        categories=b.multiselect("类别",sorted(x for x in df.category.unique() if x),key="gallery_categories")
        period=c.selectbox("历史时期",["全部","未知"]+sorted(x for x in df.historical_period.unique() if x),key="gallery_period")
        f1,f2,f3=st.columns([1,1,4])
        meaning=f1.text_input("寓意包含",key="gallery_meaning")
        context=f2.text_input("载体包含",key="gallery_context")
        def clear_gallery():
            for key,value in {"gallery_q":"","gallery_categories":[],"gallery_period":"全部","gallery_meaning":"","gallery_context":""}.items(): st.session_state[key]=value
        f3.button("清空筛选",on_click=clear_gallery)
    filtered=df.copy()
    if query: filtered=filtered[filtered.apply(lambda row:query.lower() in (" ".join(map(str,row.values))+" "+" ".join(row.visual_keywords)).lower(),axis=1)]
    if categories: filtered=filtered[filtered.category.isin(categories)]
    if period=="未知": filtered=filtered[filtered.historical_period.eq("")]
    elif period!="全部": filtered=filtered[filtered.historical_period.eq(period)]
    if meaning: filtered=filtered[filtered.cultural_meaning.str.contains(meaning,case=False,na=False)]
    if context: filtered=filtered[filtered.application_context.str.contains(context,case=False,na=False)]
    st.caption(f"{len(filtered)} 条记录 · 显示前 24 条")
    if filtered.empty: st.info("没有匹配记录。可以清空或放宽筛选条件。"); return
    for start in range(0,min(len(filtered),24),4):
        cols=st.columns(4,gap="medium")
        for col,(_,row) in zip(cols,filtered.iloc[start:start+4].iterrows()):
            with col:
                with st.container(border=True):
                    show_image(row); st.markdown(f"**{row['name']}**")
                    st.caption(f"{row['category']} · {row['historical_period'] or '时代未知'}")
                    st.write(row["cultural_meaning"] or "暂无寓意资料"); source_caption(row)
    selected=st.selectbox("查看纹样详情",filtered.pattern_id.tolist(),format_func=lambda value:df.set_index("pattern_id").loc[value,"name"])
    pattern_detail(df[df.pattern_id==selected].iloc[0])

def knowledge():
    intro("KNOWLEDGE","知识图谱浏览","关系来自实际结构化数据；文本回答引用可追溯片段，并区分数据集描述与外部核验。")
    stats=graph.stats(); metrics=st.columns(3)
    metrics[0].metric("图谱资源",stats["entities"])
    metrics[1].metric("关系三元组",sum(stats["relation_types"].values()))
    metrics[2].metric("图谱总三元组",stats["triples"])
    charts=st.columns(2)
    charts[0].bar_chart(pd.Series(stats["entity_types"],name="实体数"))
    charts[1].bar_chart(pd.Series(stats["relation_types"],name="关系数"))
    st.subheader("纹样关系探索")
    name=st.selectbox("选择纹样",df.name.tolist()) if len(df) else ""
    if name:
        relations=graph.find(name)
        if relations:
            table,diagram=st.columns([1,1.15])
            with table: st.dataframe(pd.DataFrame(relations).rename(columns={"relation":"关系","value":"关联实体"}),hide_index=True,use_container_width=True)
            with diagram:
                nodes=[]
                for idx,relation in enumerate(relations):
                    label=(relation["relation"]+"\\n"+relation["value"]).replace('"',"")
                    nodes.append(f'n{idx} [label="{label}", shape=box]; center -> n{idx};')
                safe_name=name.replace('"',"")
                st.graphviz_chart('digraph { graph [bgcolor="transparent"]; node [fontname="Microsoft YaHei"]; center [label="'+safe_name+'", shape=ellipse, style=filled, fillcolor="#EAD9BA"]; '+" ".join(nodes)+" }",use_container_width=True)
    st.divider(); st.subheader("文化资料检索")
    question=st.text_input("输入问题",placeholder="例如：缠枝莲纹的资料描述了哪些视觉特征？")
    if question:
        answer=retriever.answer(question)
        st.markdown(f"<div class='surface-note'>{answer['answer']}</div>",unsafe_allow_html=True)
        for hit in answer["evidence"]:
            with st.container(border=True):
                st.caption(f"{hit['name']} · {hit['title']} · 数据集描述 · 外部核验暂无")
                st.write(hit["text"]); st.caption(hit["source_path"])
                st.link_button("查看数据源",hit["source"])

def visual():
    intro("IMAGE ANALYSIS","视觉分析与纹样星图","颜色特征描述的是图像像素，不等于纹样语义或文化相似。聚类仅用于探索，不构成历史结论。")
    if vision_index.empty: st.warning("没有可读取的正式图片。"); return
    analyzed=analyze_features(vision_index,vision_vectors,3); silhouette=analyzed.silhouette.iloc[0]
    metrics=st.columns(4)
    metrics[0].metric("分析样本",f"{len(vision_index)} / {len(df)} 张")
    metrics[1].metric("算法","PCA + KMeans")
    metrics[2].metric("聚类数",analyzed.cluster.nunique())
    metrics[3].metric("轮廓系数",f"{silhouette:.3f}" if pd.notna(silhouette) else "样本不足")
    chart,counts=st.columns([1.8,1])
    with chart:
        try:
            import plotly.express as px
            fig=px.scatter(analyzed,x="pc1",y="pc2",color=analyzed.cluster.astype(str),hover_name="name",title="颜色特征的 PCA 投影",labels={"pc1":"主成分 1","pc2":"主成分 2","color":"聚类"})
            fig.update_layout(plot_bgcolor="#FFFEFB",paper_bgcolor="#FFFEFB",font_color="#292923",margin=dict(l=12,r=12,t=55,b=12),legend_title_text="聚类")
            st.plotly_chart(fig,use_container_width=True)
        except ImportError: st.scatter_chart(analyzed,x="pc1",y="pc2",color="cluster")
    with counts:
        st.subheader("簇样本数"); st.bar_chart(analyzed.cluster.value_counts().sort_index().rename("记录数"))
        st.caption("按当前 RGB/HSV 特征和 KMeans 标签计算。")
    with st.expander("查看图片特征明细"):
        st.dataframe(analyzed[["name","category","cluster","dominant_hex"]],hide_index=True,use_container_width=True)
    st.divider(); st.subheader("颜色近邻与提取色卡")
    upload=st.file_uploader("上传一张临时参考图",type=["png","jpg","jpeg"],help="图片只在本地计算，不会传到外部服务。")
    query_id=st.selectbox("或选择图鉴图片",[""]+vision_index.pattern_id.tolist(),format_func=lambda value:"选择纹样" if not value else vision_index.set_index("pattern_id").loc[value,"name"])
    query=upload or (df.set_index("pattern_id").loc[query_id,"image_path"] if query_id else None)
    if query:
        palette=extract_features(query)["palette_hex"]
        st.markdown("　".join(f"<span style='display:inline-block;background:{color};width:74px;height:42px;border:1px solid #cbc5b8;border-radius:3px;vertical-align:middle' title='{color}'></span>" for color in palette),unsafe_allow_html=True)
        st.code(" · ".join(palette))
        st.download_button("下载色卡 JSON",json.dumps({"source":"图片像素颜色量化","colors":palette},ensure_ascii=False,indent=2),"palette.json","application/json")
        neighbors=visual_neighbors(query,vision_index,vision_vectors,5,query_id or None)
        st.dataframe(pd.DataFrame(neighbors)[["name","category","distance","similarity"]] if neighbors else pd.DataFrame(),hide_index=True,use_container_width=True)

def agent_page():
    intro("DESIGN ASSISTANT","设计辅助智能体","六步真实工具链：需求解析、条件检索、知识图谱、资料证据、颜色近邻与可解释排序。")
    request=st.text_area("设计需求",value="想设计一套宋代风格的文房茶具，希望整体简洁、雅致，寓意清雅。",height=100)
    upload=st.file_uploader("可选：上传颜色参考图（仅本地计算）",type=["png","jpg","jpeg"],key="agent-upload")
    wc=st.columns(3)
    ws=wc[0].slider("结构条件",0.0,1.0,0.55,0.05)
    wt=wc[1].slider("文本证据",0.0,1.0,0.30,0.05)
    wv=wc[2].slider("视觉颜色",0.0,1.0,0.15,0.05)
    total=ws+wt+wv; weights={"structured":ws/total if total else 0,"text":wt/total if total else 0,"visual":wv/total if total else 0}
    if st.button("运行检索与推荐",type="primary"):
        st.session_state.agent_result=DesignAgent(df,graph,retriever,vision_index,vision_vectors,weights).run(request,upload,5)
    result=st.session_state.get("agent_result")
    if result:
        st.subheader("工具调用记录")
        with st.expander("查看各工具返回",expanded=False): st.json(result["trace"])
        if result["message"]: st.warning(result["message"])
        for rank,row in enumerate(result["candidates"],1):
            with st.container(border=True):
                image_col,content_col=st.columns([.8,1.5],gap="large")
                with image_col: show_image(row)
                with content_col:
                    st.subheader(f"{rank:02d}　{row['name']}")
                    st.markdown(f"<span class='result-score'>综合 {row['score']:.3f}</span>　结构 {row['structured_score']:.2f}　文本 {row['text_score']:.2f}　颜色 {row['visual_score']:.2f}",unsafe_allow_html=True)
                    st.write("**实际匹配**　"+("；".join(row["matched"]) or "无明确匹配条件"))
                    st.write("**未满足条件**　"+("；".join(row["unmatched"]) or "无"))
                    st.progress(row["completeness"],text=f"数据完整度 {row['completeness']:.0%}")
                    for risk in row["risks"]: st.warning(risk)
                    if row.get("evidence"):
                        ev=row["evidence"]; st.caption(f"数据集描述 · 外部核验暂无 · {ev['title']}")
                        st.write(ev["text"]); st.link_button("打开证据来源",ev["source"])
                    else: st.caption("没有检索到文化证据")
                    st.button("以此纹样作为创作参考",key=f"agent-create-{row['pattern_id']}",on_click=set_creation_reference,args=(row,))

def studio():
    intro("AI PATTERN STUDIO","AI 纹样创作室","从主题与设计约束生成新的纹样提案。模型输出会单独标注，不会写入正式纹样库或文化知识证据。")
    n1,n2=st.columns([1.4,1])
    with n1: st.markdown("<div class='surface-note'>AI 图像是设计探索稿，不代表历史时期、传统原型或文化寓意已经核验。</div>",unsafe_allow_html=True)
    with n2:
        if bailian_key: st.success("阿里云百炼 · 通义万相已配置")
        elif openai_key: st.success("OpenAI Images API 已配置")
        else: st.info("未配置图像 API 密钥；可使用本地程序化 SVG 生成。")
    patterns={row["pattern_id"]:row for _,row in df.iterrows()}
    current_ref=st.session_state.get("studio_reference_id","")
    ref_options=[""]+list(patterns)
    if current_ref not in ref_options: current_ref=""
    with st.container(border=True):
        st.subheader("设计简报")
        c1,c2=st.columns([1.2,1])
        theme=c1.text_input("纹样主题",value="缠枝与花叶的连续纹样",max_chars=80,help="填写主题或核心意象，不要把未经核验的年代当作事实。")
        style=c2.selectbox("风格方向",["传统装饰","现代简约","新中式"])
        c3,c4=st.columns([1,1])
        scene=c3.selectbox("应用场景",["茶具","织物","包装","文房器物","家居装饰","自由应用"])
        palette_names=["墨黑","朱砂","黛青","松绿","月白","鎏金","藕粉","石青"]
        palette_choice=c4.multiselect("配色（最多 5 色）",palette_names,default=["月白","黛青","朱砂"],max_selections=5)
        palette_map={"墨黑":"#292923","朱砂":"#9E4037","黛青":"#3E5C64","松绿":"#68746A","月白":"#F2EFE7","鎏金":"#B49A64","藕粉":"#C99291","石青":"#547B91"}
        palette=[palette_map[color] for color in palette_choice]
        requirements=st.text_area("补充设计要求",placeholder="例如：边缘清晰、留白较多、适合小面积印制。",max_chars=500,height=80)
        selected_ref=st.selectbox("可选参考纹样",ref_options,index=ref_options.index(current_ref),format_func=lambda value:"不使用参考" if not value else patterns[value]["name"],key="studio_reference_select")
    reference=patterns[selected_ref] if selected_ref else None
    if reference is not None:
        a,b=st.columns([.55,1.45])
        with a: show_image(reference)
        with b:
            st.markdown(f"**检索参考 · {reference['name']}**")
            st.write("视觉词："+("、".join(reference["visual_keywords"]) or "未提供"))
            st.write("来源描述："+(reference["summary"] or "未提供"))
            st.caption(f"来源：{display_source_name(reference['source_name'])} · ID：{reference['pattern_id']} · {reference['license']}")
            st.caption("只作为提示词启发；参考原图不会上传，文字仍是未经独立核验的数据集描述。")
    st.subheader("生成方式")
    generation_config=cfg.get("image_generation",{})
    available_providers=[]
    if bailian_key: available_providers.append("阿里云百炼 · 通义万相")
    if openai_key: available_providers.append("OpenAI Images API")
    provider_options=available_providers or ["阿里云百炼 · 通义万相"]
    selected_provider=st.selectbox("AI 图像服务",provider_options,disabled=not bool(available_providers))
    if selected_provider.startswith("阿里云"):
        provider_key=bailian_key
        model=generation_config.get("model","wanx2.1-t2i-turbo")
        st.caption(f"百炼模型：{model} · 地域：{generation_config.get('region','beijing')} · {generation_config.get('size','1024x1024')}。按阿里云当前价格计费；只发送本次提示词，不上传参考原图。")
    else:
        provider_key=openai_key
        model=generation_config.get("openai_model","gpt-image-1")
        st.caption(f"OpenAI 模型：{model} · {generation_config.get('size','1024x1024')}。按服务商当前价格计费；只发送本次提示词。")
    ac,sc=st.columns(2)
    generate_ai=ac.button("生成 AI 纹样",type="primary",disabled=not bool(provider_key),use_container_width=True)
    generate_svg=sc.button("生成程序化 SVG 备用图",use_container_width=True)
    if not available_providers: st.caption("百炼用户请配置 DASHSCOPE_API_KEY；也支持 OPENAI_API_KEY。无密钥时程序化 SVG 和其他页面仍可使用。")
    def save_output(result,prompt,parameters):
        output_dir=Path(os.environ.get("PATTERN_GENERATION_DIR", project_path("data/generated")))
        artifact=save_generation(result,prompt,parameters,output_dir)
        st.session_state.studio_output=artifact; st.session_state.studio_error=""
    if generate_ai:
        try:
            prompt,parameters=build_pattern_prompt(theme,style,palette,scene,requirements,reference)
            with st.spinner("正在请求图像生成服务……"):
                generation_config=cfg.get("image_generation",{})
                if selected_provider.startswith("阿里云"):
                    result=BailianImageProvider(
                        provider_key, model=model, region=generation_config.get("region","beijing"),
                        timeout=generation_config.get("timeout_seconds",120),
                        poll_interval=generation_config.get("poll_interval_seconds",2),
                    ).generate(prompt,size=generation_config.get("size","1024x1024"))
                else:
                    result=OpenAIImageProvider(provider_key,model=model,timeout=generation_config.get("timeout_seconds",120),quality=generation_config.get("quality","low")).generate(prompt,size=generation_config.get("size","1024x1024"))
            save_output(result,prompt,parameters)
        except (ValueError,GenerationError,OSError) as exc: st.session_state.studio_error=str(exc)
    if generate_svg:
        try:
            prompt,parameters=build_pattern_prompt(theme,style,palette,scene,requirements,reference)
            svg=generate_programmatic_svg(theme,style,palette,scene,requirements)
            result=GenerationResult(svg,"image/svg+xml","Programmatic SVG","pattern-tile-v1","720x360","not_applicable")
            save_output(result,prompt,parameters)
        except (ValueError,OSError) as exc: st.session_state.studio_error=str(exc)
    if st.session_state.get("studio_error"): st.error(st.session_state.studio_error)
    output=st.session_state.get("studio_output")
    if output:
        st.divider()
        st.markdown(f"<div class='eyebrow'>{output['label']}</div>",unsafe_allow_html=True)
        st.subheader("创作结果")
        if output["mime_type"] == "image/svg+xml":
            components.html(output["image_bytes"].decode("utf-8"),height=390,scrolling=False)
        else:
            st.image(output["image_bytes"],use_container_width=True)
        st.caption(f"Provider：{output['provider']} · 模型/程序：{output['model']} · 尺寸：{output['size']} · 质量：{output['quality']}")
        st.write("**设计思路**　主题、风格、配色和场景组合为设计提案；参考纹样只贡献可追溯的视觉词和描述。")
        p=output["parameters"]
        st.write("**对应用户要求**　"+f"主题：{p['theme']}；风格：{p['style']}；场景：{p['scene']}；配色：{'、'.join(p['palette'])}")
        ref=p.get("reference")
        if ref:
            st.caption(f"参考来源：{display_source_name(ref['source_name'])} · {ref['pattern_id']} · {ref['source_url']}")
            if not ref.get("historical_period"): st.warning("参考纹样没有历史时期字段；生成结果不作时代归属，尚未核验。")
        else: st.caption("未使用检索参考纹样。")
        st.markdown("**完整提示词**"); st.code(output["prompt"],language=None)
        st.download_button("下载生成图",output["image_bytes"],Path(output["image_path"]).name,output["mime_type"],type="primary")
        metadata={k:v for k,v in output.items() if k not in {"image_bytes","image_path","metadata_path"}}
        st.download_button("下载生成参数 JSON",json.dumps(metadata,ensure_ascii=False,indent=2),"generation_parameters.json","application/json")

def methods():
    intro("METHODS","数据与方法说明","查看真实数据覆盖、算法结果、许可边界和图像生成模式。")
    audit=audit_patterns(df)
    metrics=st.columns(4)
    for col,label,value in zip(metrics,["正式记录","可用图片","缺图","外部文化证据"],[audit["records"],audit["available_images"],audit["missing_images"],"暂无"]): col.metric(label,value)
    st.subheader("图片数据变化")
    st.dataframe(pd.DataFrame([{"阶段":"扩充前","记录":100,"可用图片":8,"缺失图片":92},{"阶段":"当前","记录":audit["records"],"可用图片":audit["available_images"],"缺失图片":audit["missing_images"]}]),hide_index=True,use_container_width=True)
    report=project_path("data/processed/visual_analysis.json")
    if report.is_file():
        vr=json.loads(report.read_text(encoding="utf-8"))
        st.caption(f"视觉实测：样本 {vr['samples']} 张 · PCA 2 维 · KMeans k={vr['kmeans_clusters']} · 轮廓系数 {vr['silhouette']:.6f}")
    st.subheader("图像生成 Provider")
    st.markdown("""- 默认 AI Provider：阿里云百炼通义万相，使用异步任务生成并下载 1024×1024 PNG；OpenAI Images API 作为可选 Provider 保留。
- 只发送用户本次填写的提示词和经选择的参考纹样文本字段；本地图片、整个数据集和知识库不会上传。
- 百炼使用 `DASHSCOPE_API_KEY`，OpenAI 使用 `OPENAI_API_KEY`；均通过环境变量或 `.streamlit/secrets.toml` 配置。没有密钥时，AI 按钮不可用，检索与程序化 SVG 仍可使用。
- SVG 备用方案由本地确定性几何规则生成，标记为“程序化生成”，不是 AI 图像。
- AI 生成会按服务商价格计费；发起前应查看账户当前价格和额度。本应用不保证价格或免费额度。
- 生成文件写入 `data/generated/`，旁边保存提示词、参数、Provider 和参考纹样 ID；不会加入正式纹样库或知识图谱。
""")
    st.subheader("数据来源与许可")
    st.write("《中国传统纹样图鉴》· 100 条记录 · 100 张数据集卡片图。图片与文字采用 CC BY-NC 4.0 许可；项目保留原始记录 ID、来源链接与许可信息，支持完整的数据追溯。")
    st.link_button("查看《中国传统纹样图鉴》原始仓库","https://github.com/dososo/chinese-traditional-patterns")
    st.download_button("下载当前审计 JSON",json.dumps(audit,ensure_ascii=False,indent=2),"data_audit.json","application/json")

if df.empty:
    st.error("未找到正式数据。请按 README 准备数据后重试。")
else:
    with st.sidebar:
        st.markdown("<div class='eyebrow'>PATTERN INTELLIGENCE</div>",unsafe_allow_html=True)
        st.title("纹样知策"); st.caption("东方纹样 · 数字设计工作台"); st.divider()
        page=st.radio("工作空间",PAGES,key="navigation",label_visibility="collapsed")
        st.divider(); st.caption("当前数据")
        st.write(f"{len(df)} 条纹样 · {len(vision_index)} 张可分析图片")
        st.caption("文化资料：数据集描述，未独立核验")
    routes={"首页":home,"纹样图鉴与详情":gallery,"知识图谱":knowledge,"视觉分析":visual,"设计辅助智能体":agent_page,"AI 纹样创作室":studio,"数据与方法":methods}
    routes[page]()
