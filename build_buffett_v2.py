#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巴菲特知识库 v2 前端构建器 —— chian.io 视觉风格
=================================================
在不改变原有前端（巴菲特投资智慧.html）的前提下，生成一个采用
chian.io/projects/buffett-letters 视觉风格的新前端：
  - 深色固定侧边栏（#1c1c1c）+ 暖米色主区（#f5f4f0）
  - 衬线大标题（ui-serif/Georgia/宋体）+ 无衬线正文
  - 大写间距标签、发丝线分隔、黑色实心按钮、金色点缀
  - 保留原有全部功能：分类/年代/标签筛选、全文搜索、阅读、
    划线笔记、AI 讨论、背景解释、编辑风索引纵览

用法：
  python3 build_buffett_v2.py
输出：
  巴菲特投资智慧-v2.html（自包含单文件，与原文件并存）
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from build_buffett_app import build, APP_JS  # noqa: E402

OUT_V2 = os.path.join(HERE, "巴菲特投资智慧-v2.html")

# ================================================================ CSS
V2_CSS = r"""
:root{
  --sidebar-bg:#1c1c1c;
  --sidebar-text:#f5f4f0;
  --sidebar-muted:#7a776f;
  --sidebar-hover:#2a2a28;
  --sidebar-active:#f5f4f0;
  --sidebar-active-text:#1c1c1c;
  --sidebar-border:#2e2d2a;

  --bg:#f5f4f0;
  --panel:#ffffff;
  --ink:#1c1c1c;
  --ink2:#6b6b66;
  --ink3:#9a9a92;
  --line:#e0ddd4;
  --line2:#ebe8df;

  --accent:#b8963e;
  --accent-hover:#a07f2e;
  --black:#1c1c1c;
  --hl:#ffe9a8;
  --hl2:#bfe3ff;
  --hl3:#ffd9cc;

  --serif:ui-serif,Georgia,Cambria,"Times New Roman",Times,"Songti SC","STSong","SimSun",serif;
  --sans:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
[hidden]{display:none !important}
html{scroll-behavior:smooth}
body{
  background:var(--bg);color:var(--ink);
  font:15px/1.65 var(--sans);
  -webkit-font-smoothing:antialiased;
}
button{font:inherit;color:inherit;background:none;border:none;cursor:pointer}
select,input,textarea{font:inherit;color:inherit}
a{color:var(--ink);text-decoration:none;transition:color .15s}
a:hover{color:var(--accent)}
::-webkit-scrollbar{width:8px;height:8px}
::-webkit-scrollbar-thumb{background:#cfcbc0;border-radius:4px}
::-webkit-scrollbar-thumb:hover{background:#b8b4a8}
::-webkit-scrollbar-track{background:transparent}

/* ==================== 布局 ==================== */
#layout{display:flex;min-height:100vh}

/* ---- 深色侧边栏 ---- */
#sidebar{
  width:280px;flex:0 0 280px;
  background:var(--sidebar-bg);color:var(--sidebar-text);
  position:fixed;top:0;left:0;bottom:0;z-index:60;
  overflow-y:auto;overflow-x:hidden;
  display:flex;flex-direction:column;
  padding:0;
}
#sidebar::-webkit-scrollbar{width:6px}
#sidebar::-webkit-scrollbar-thumb{background:#3a3935}
.sb-brand{
  padding:28px 24px 20px;cursor:pointer;
  border-bottom:1px solid var(--sidebar-border);
}
.sb-brand:hover .sb-brand-title{color:#fff}
.sb-brand-title{
  font:700 17px/1.3 var(--sans);color:var(--sidebar-text);
  letter-spacing:.2px;
}
.sb-brand-sub{
  font-size:12px;color:var(--sidebar-muted);margin-top:3px;
  letter-spacing:.3px;
}
.sb-search{padding:16px 20px 12px;position:relative}
.sb-search input{
  width:100%;padding:9px 32px 9px 34px;
  background:#262523;border:1px solid #33322f;border-radius:8px;
  color:var(--sidebar-text);font-size:13px;outline:none;
  transition:border-color .15s,background .15s;
}
.sb-search input::placeholder{color:#6a6863}
.sb-search input:focus{border-color:var(--accent);background:#2c2b28}
.sb-search::before{
  content:"";position:absolute;left:32px;top:50%;transform:translateY(-50%);
  width:14px;height:14px;opacity:.45;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23f5f4f0' stroke-width='2'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='M21 21l-4.3-4.3'/%3E%3C/svg%3E");
  background-size:contain;background-repeat:no-repeat;
}
#qCount{
  position:absolute;right:30px;top:50%;transform:translateY(-50%);
  font-size:11px;color:var(--sidebar-muted);pointer-events:none;
}

/* 侧边栏导航 */
.sb-nav{padding:8px 14px 4px}
.sb-nav-item{
  display:flex;align-items:center;gap:10px;width:100%;
  padding:9px 12px;border-radius:7px;
  font-size:13px;font-weight:600;color:var(--sidebar-muted);
  text-align:left;letter-spacing:.3px;transition:all .15s;
}
.sb-nav-item:hover{background:var(--sidebar-hover);color:var(--sidebar-text)}
.sb-nav-item.active{
  background:var(--sidebar-active);color:var(--sidebar-active-text);
}
.sb-nav-item .ico{width:16px;text-align:center;font-size:14px;opacity:.8}

/* 侧边栏分组 */
.sb-sec{padding:10px 14px 4px}
.sb-title{
  font-size:10.5px;font-weight:700;color:var(--sidebar-muted);
  letter-spacing:1.8px;text-transform:uppercase;
  margin:8px 10px 7px;
  display:flex;justify-content:space-between;align-items:center;
}
.sb-title-range{font-weight:400;letter-spacing:0;text-transform:none}
.sb-item{
  display:flex;align-items:center;justify-content:space-between;gap:6px;width:100%;
  padding:6px 12px;border-radius:6px;
  font-size:13px;color:#b0ada5;text-align:left;transition:all .12s;
}
.sb-item:hover{background:var(--sidebar-hover);color:var(--sidebar-text)}
.sb-item.active{
  background:var(--sidebar-active);color:var(--sidebar-active-text);font-weight:600;
}
.sb-item .n{
  font-size:11px;color:var(--sidebar-muted);
  background:#2a2926;padding:1px 7px;border-radius:10px;min-width:22px;text-align:center;
}
.sb-item.active .n{background:#e0ddd4;color:var(--ink)}
.sb-item .ico{width:16px;text-align:center;font-size:12px;opacity:.6;margin-right:2px}
.sb-item.has-ico{padding-left:10px}
.sb-item.has-ico>span:first-child{display:flex;align-items:center;gap:8px}

/* 标签云 */
.tag-cloud{display:flex;flex-wrap:wrap;gap:4px;padding:0 8px}
.tag-chip{
  font-size:11.5px;padding:3px 9px;border-radius:20px;
  border:1px solid #33322f;background:transparent;
  color:#b0ada5;cursor:pointer;white-space:nowrap;transition:all .12s;
}
.tag-chip:hover{border-color:var(--accent);color:var(--accent)}
.tag-chip.active{background:var(--accent);border-color:var(--accent);color:#fff}

/* 复选框 */
.sb-check{
  display:flex;align-items:center;gap:8px;padding:5px 12px;
  font-size:13px;color:#b0ada5;cursor:pointer;border-radius:6px;
}
.sb-check:hover{background:var(--sidebar-hover);color:var(--sidebar-text)}
.sb-check input{accent-color:var(--accent);width:14px;height:14px}

/* 分类索引（xlsx 五维） */
.idx-group{margin:1px 0}
.idx-gtitle{
  display:flex;justify-content:space-between;align-items:center;width:100%;
  padding:6px 12px;border-radius:6px;
  font-size:12.5px;font-weight:600;color:#b0ada5;
  background:transparent;cursor:pointer;text-align:left;transition:all .12s;
}
.idx-gtitle:hover{background:var(--sidebar-hover);color:var(--sidebar-text)}
.idx-gtitle .n{font-size:10.5px;font-weight:400;color:var(--sidebar-muted)}
.idx-items{display:none;padding:2px 0 4px}
.idx-group.open .idx-items{display:block}
.idx-items .sb-item{font-size:12px;padding:4px 12px 4px 20px;border-radius:5px}
.idx-items .sb-item .n{font-size:10px;padding:0 6px}

.sb-foot{
  margin-top:auto;padding:16px 20px 20px;
  border-top:1px solid var(--sidebar-border);
  font-size:11px;color:var(--sidebar-muted);line-height:1.7;
}
.sb-switch{
  display:inline-block;margin-top:8px;color:var(--sidebar-muted);
  font-size:11px;text-decoration:none;border-bottom:1px solid #3a3935;
  padding-bottom:1px;transition:all .15s;
}
.sb-switch:hover{color:var(--accent);border-bottom-color:var(--accent)}

/* 侧边栏底部：与巴菲特对话 */
.sb-talk{
  margin:8px 14px 12px;padding:14px 14px;
  border:1px solid #33322f;border-radius:10px;
  background:linear-gradient(135deg,#232220,#1c1c1c);
  cursor:pointer;transition:border-color .15s;text-align:left;
}
.sb-talk:hover{border-color:var(--accent)}
.sb-talk-title{
  font:700 13px/1.3 var(--serif);color:var(--sidebar-text);
  display:flex;align-items:center;gap:7px;
}
.sb-talk-beta{
  font-size:9px;font-weight:700;letter-spacing:1px;
  color:var(--accent);border:1px solid var(--accent);
  padding:1px 5px;border-radius:3px;text-transform:uppercase;
}
.sb-talk-desc{font-size:11px;color:var(--sidebar-muted);margin-top:5px;line-height:1.5}

/* ---- 主内容区 ---- */
#mainCol{
  margin-left:280px;flex:1;min-width:0;
  display:flex;flex-direction:column;min-height:100vh;
}
#topbar{
  position:sticky;top:0;z-index:50;
  display:flex;align-items:center;gap:10px;
  padding:10px 32px;
  background:rgba(245,244,240,.88);backdrop-filter:blur(10px);
  border-bottom:1px solid var(--line);
}
#menuBtn{display:none}
.top-actions{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-left:auto}
.tbtn{
  padding:6px 12px;border:1px solid var(--line);border-radius:7px;
  background:var(--panel);font-size:12.5px;color:var(--ink2);
  display:inline-flex;align-items:center;gap:5px;white-space:nowrap;
  transition:all .12s;
}
.tbtn:hover{border-color:var(--ink);color:var(--ink)}
.tbtn.active{background:var(--ink);border-color:var(--ink);color:#fff}
select.tbtn{-webkit-appearance:none;appearance:none;padding-right:26px;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%236b6b66'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 10px center;cursor:pointer}

#main{flex:1;padding:0 32px 60px;max-width:1100px;width:100%}

/* ==================== 主页 ==================== */
#home{padding-top:0}

/* Hero */
.home-hero{
  padding:56px 0 40px;
  display:grid;grid-template-columns:1.4fr 1fr;gap:48px;align-items:start;
  border-bottom:1px solid var(--line);
}
.hh-eyebrow{
  font-size:11px;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;
  color:var(--ink3);margin-bottom:20px;
}
.home-hero h1{
  font:700 52px/1.08 var(--serif);color:var(--ink);
  letter-spacing:-.5px;margin-bottom:0;
}
.home-hero h1 .accent{color:var(--accent)}
.hh-right{padding-top:8px}
.hh-sub{
  color:var(--ink2);font-size:14.5px;line-height:1.75;margin-bottom:24px;
}
.hh-btn{
  display:inline-flex;align-items:center;gap:8px;
  padding:13px 26px;background:var(--black);color:#fff;
  font-size:12.5px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
  border-radius:0;transition:background .15s;
}
.hh-btn:hover{background:#333;color:#fff}
.hh-btn .arr{transition:transform .15s}
.hh-btn:hover .arr{transform:translateX(3px)}

/* 统计行 */
.hh-stats{
  display:grid;grid-template-columns:repeat(4,1fr);
  border:1px solid var(--line);border-radius:0;
  margin:32px 0;background:var(--panel);
}
.hh-stats>div{
  padding:22px 20px;text-align:center;
  border-right:1px solid var(--line);
}
.hh-stats>div:last-child{border-right:none}
.hh-stats b{
  display:block;font:700 32px/1.1 var(--serif);color:var(--ink);
}
.hh-stats span{
  display:block;font-size:10.5px;font-weight:600;letter-spacing:1.5px;
  text-transform:uppercase;color:var(--ink3);margin-top:5px;
}

/* 主页搜索 */
.hh-search{display:none}

/* 分区标题 */
.home-sec{margin-top:48px}
.home-sec>h2{
  font:700 24px/1.3 var(--serif);color:var(--ink);margin-bottom:6px;
}
.home-sec>h2 .n{font-size:12px;color:var(--ink3);font-weight:400;margin-left:8px}
.home-sec .sec-eyebrow{
  font-size:10.5px;font-weight:600;letter-spacing:2px;text-transform:uppercase;
  color:var(--ink3);margin-bottom:8px;
}
.home-sec .sec-sub{font-size:13.5px;color:var(--ink2);margin-bottom:20px}

/* 快速浏览卡片 */
.home-grid{
  display:grid;grid-template-columns:repeat(3,1fr);gap:16px;
}
.home-tile{
  text-align:left;padding:24px 22px;
  border:1px solid var(--line);background:var(--panel);
  border-radius:0;transition:all .15s;cursor:pointer;position:relative;
}
.home-tile:hover{border-color:var(--ink);transform:translateY(-1px)}
.ht-ic{font-size:20px;margin-bottom:12px;opacity:.7}
.ht-name{font:700 17px/1.3 var(--serif);color:var(--ink);margin-bottom:5px}
.ht-desc{font-size:12.5px;color:var(--ink3);letter-spacing:.3px}
.ht-count{
  position:absolute;top:18px;right:18px;
  font-size:10px;font-weight:600;letter-spacing:1px;
  color:var(--ink3);border:1px solid var(--line);padding:2px 8px;border-radius:3px;
}

/* 四宫格入口卡片（Letters/Concepts/Companies/People 风格） */
.feature-grid{
  display:grid;grid-template-columns:repeat(2,1fr);gap:20px;margin-top:24px;
}
.feature-card{
  text-align:left;padding:30px 28px;
  border:1px solid var(--line);background:transparent;
  cursor:pointer;transition:all .15s;position:relative;
}
.feature-card:hover{border-color:var(--ink);background:var(--panel)}
.fc-icon{
  width:36px;height:36px;display:flex;align-items:center;justify-content:center;
  font-size:18px;color:var(--ink2);margin-bottom:18px;
}
.fc-label{
  font-size:10px;font-weight:600;letter-spacing:2px;text-transform:uppercase;
  color:var(--ink3);margin-bottom:8px;
}
.fc-title{font:700 22px/1.3 var(--serif);color:var(--ink);margin-bottom:8px}
.fc-desc{font-size:13px;color:var(--ink2);line-height:1.65;margin-bottom:18px}
.fc-link{
  font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
  color:var(--ink);display:inline-flex;align-items:center;gap:6px;
}
.feature-card:hover .fc-link{color:var(--accent)}
.fc-badge{
  position:absolute;top:24px;right:24px;
  font-size:10px;letter-spacing:1px;color:var(--ink3);
  border:1px solid var(--line);padding:2px 8px;
}

/* Talk to Buffett 横条 */
.talk-banner{
  display:flex;align-items:center;gap:28px;
  padding:24px 28px;margin-top:32px;
  border-left:3px solid var(--accent);
  background:var(--panel);
}
.tb-left{flex:0 0 auto}
.tb-title{font:700 20px/1.3 var(--serif);color:var(--ink);display:flex;align-items:center;gap:10px}
.tb-beta{
  font-size:9px;font-weight:700;letter-spacing:1px;color:var(--accent);
  border:1px solid var(--accent);padding:1px 5px;border-radius:3px;text-transform:uppercase;
}
.tb-sub{font-size:11px;letter-spacing:1.5px;text-transform:uppercase;color:var(--ink3);margin-top:4px}
.tb-desc{flex:1;font-size:13.5px;color:var(--ink2);line-height:1.65}
.tb-btn{
  flex:0 0 auto;font-size:11px;font-weight:700;letter-spacing:1.5px;
  text-transform:uppercase;color:var(--accent);
  display:inline-flex;align-items:center;gap:7px;white-space:nowrap;
}
.tb-btn:hover{color:var(--accent-hover)}

/* 必读经典 / 最新信件 列表 */
.home-list{border-top:1px solid var(--line)}
.home-row{
  display:grid;grid-template-columns:72px 1fr auto;gap:16px;align-items:center;
  padding:16px 4px;border-bottom:1px solid var(--line);
  cursor:pointer;transition:background .12s;
}
.home-row:hover{background:rgba(0,0,0,.015)}
.hr-year{
  font-size:11px;font-weight:600;letter-spacing:1px;color:var(--ink3);
  text-transform:uppercase;
}
.hr-title{font:700 15px/1.4 var(--serif);color:var(--ink)}
.home-row:hover .hr-title{color:var(--accent)}
.hr-why{font-size:12.5px;color:var(--ink2);text-align:right;max-width:280px}

/* 热门标签 */
.home-chips{display:flex;flex-wrap:wrap;gap:8px}
.home-chips .tag-chip{
  border-color:var(--line);color:var(--ink2);background:var(--panel);
  font-size:12px;padding:5px 12px;
}
.home-chips .tag-chip:hover{border-color:var(--accent);color:var(--accent)}

/* 继续阅读 */
.home-last{
  display:flex;align-items:center;gap:14px;margin-top:32px;
  padding:18px 22px;border:1px solid var(--line);background:var(--panel);
  cursor:pointer;transition:border-color .15s;
}
.home-last:hover{border-color:var(--accent)}
.hl-ic{font-size:22px}
.hl-title{font:700 14px/1.4 var(--serif);color:var(--ink)}
.hl-time{font-size:12px;color:var(--ink3);margin-top:2px}
.home-last .arr{margin-left:auto;color:var(--ink3);font-size:18px}

/* 概念频率标签（The Intellectual Framework 风格） */
.concept-tags{display:flex;flex-wrap:wrap;gap:8px}
.concept-tag{
  display:inline-flex;align-items:center;gap:7px;
  padding:7px 14px;border:1px solid var(--line);background:var(--panel);
  font-size:13px;color:var(--ink);cursor:pointer;transition:all .12s;
}
.concept-tag:hover{border-color:var(--ink)}
.concept-tag .ct-count{
  font-size:11px;color:var(--ink3);font-weight:600;
  background:var(--bg);padding:1px 7px;border-radius:10px;
}

/* ==================== 文库列表 ==================== */
#library{padding-top:24px}
#libHead{
  display:flex;align-items:baseline;gap:14px;
  padding-bottom:16px;margin-bottom:20px;border-bottom:1px solid var(--line);
}
#libTitle{font:700 28px/1.2 var(--serif);color:var(--ink)}
#libCount{font-size:13px;color:var(--ink3)}

/* 分类索引横幅 */
.idx-banner{
  background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);
  padding:18px 48px 18px 20px;margin-bottom:20px;position:relative;
}
.idx-banner h3{font:700 17px/1.5 var(--serif);margin-bottom:8px;color:var(--ink)}
.idx-banner .idx-rng{font-size:12px;color:var(--ink3);font-weight:400;margin-left:6px}
.idx-banner p{font-size:13px;color:var(--ink2);line-height:1.8;margin:.35em 0}
.idx-banner p b{color:var(--ink);font-weight:700}
.idx-banner .idx-rep{color:var(--ink2);font-size:12.5px}
.idx-banner .idx-sum{font-size:13.5px}
.idx-banner .idx-chips{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-top:9px}
.idx-banner .idx-lbl{font-size:12px;color:var(--ink2);font-weight:600}
.idx-close{
  position:absolute;top:12px;right:14px;color:var(--ink3);font-size:15px;
  padding:2px 7px;border-radius:6px;
}
.idx-close:hover{color:#b91c1c;background:#fde8e8}
.r-idx{
  display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-top:7px;font-size:12px;
  color:var(--ink2);background:var(--panel);border:1px solid var(--line);padding:6px 12px;
}
.r-idx b{color:var(--accent)}
.r-idx .mini-tag{cursor:pointer}

/* 卡片 */
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.card{
  padding:22px 22px 20px;border:1px solid var(--line);background:var(--panel);
  cursor:pointer;transition:all .15s;display:flex;flex-direction:column;
}
.card:hover{border-color:var(--ink);transform:translateY(-1px)}
.card-head{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.badge{
  font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;
  padding:2px 8px;border-radius:3px;
}
.badge.cat{background:var(--bg);color:var(--ink2);border:1px solid var(--line)}
.badge.year{background:var(--ink);color:#fff}
.badge.kind{background:var(--accent);color:#fff}
.card-note{font-size:13px;margin-left:auto}
.card-fav{font-size:15px;color:var(--ink3);margin-left:2px}
.card-fav:hover{color:var(--accent)}
.card-title{font:700 17px/1.35 var(--serif);margin-bottom:8px}
.card-title a{color:var(--ink)}
.card-title a:hover{color:var(--accent)}
.card-excerpt{
  font-size:13px;color:var(--ink2);line-height:1.65;
  display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;
  flex:1;
}
.card-tags{display:flex;flex-wrap:wrap;gap:5px;margin-top:12px}
.mini-tag{
  font-size:11px;padding:2px 8px;border-radius:20px;
  background:var(--bg);color:var(--ink2);border:1px solid var(--line2);
}
button.mini-tag{cursor:pointer}
button.mini-tag:hover{border-color:var(--accent);color:var(--accent)}

/* 列表行 */
.rows{display:flex;flex-direction:column}
.row{
  display:grid;grid-template-columns:auto auto 1fr auto;gap:12px;align-items:center;
  padding:13px 14px;border-bottom:1px solid var(--line);cursor:pointer;transition:background .12s;
}
.row:hover{background:rgba(0,0,0,.015)}
.r-title{font:600 14.5px/1.4 var(--serif);color:var(--ink)}
.row:hover .r-title{color:var(--accent)}
.r-meta{font-size:12px;color:var(--ink3);text-align:right}
.empty{text-align:center;padding:60px 20px;color:var(--ink3)}
.empty .big{font-size:42px;margin-bottom:12px}

/* ==================== 阅读器 ==================== */
#reader{padding-top:0}
#progress{
  position:fixed;top:0;left:280px;right:0;height:3px;background:var(--accent);
  width:0;z-index:100;transition:width .1s;
}
.reader-top{
  display:flex;align-items:flex-start;gap:16px;
  padding:28px 0 20px;border-bottom:1px solid var(--line);margin-bottom:28px;
}
.reader-title{flex:1;min-width:0}
#rTitle{font:700 30px/1.25 var(--serif);color:var(--ink);margin-bottom:10px}
.r-meta{font-size:12.5px;color:var(--ink3);display:flex;gap:12px;flex-wrap:wrap}
.r-tags{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}
.r-actions{display:flex;gap:6px;flex-shrink:0}
.reader-body{display:grid;grid-template-columns:1fr 320px;gap:40px;align-items:start}
#article{
  font:15px/1.8 var(--serif);color:var(--ink);
  max-width:720px;
}
#article h1{font:700 24px/1.3 var(--serif);margin:28px 0 14px}
#article h2{font:700 20px/1.3 var(--serif);margin:26px 0 12px;padding-bottom:6px;border-bottom:1px solid var(--line)}
#article h3{font:700 17px/1.3 var(--serif);margin:22px 0 10px}
#article h4{font:700 15px/1.3 var(--serif);margin:18px 0 8px}
#article p{margin:0 0 14px}
#article ul,#article ol{margin:0 0 14px 22px}
#article li{margin:5px 0}
#article blockquote{
  margin:0 0 16px;padding:12px 18px;
  border-left:3px solid var(--accent);background:var(--panel);
  color:var(--ink2);font-size:14px;
}
#article blockquote p:last-child{margin-bottom:0}
#article code{
  font:13px var(--mono);background:var(--line2);padding:2px 6px;border-radius:4px;
}
#article pre{
  background:var(--sidebar-bg);color:#e0ddd4;padding:14px 18px;border-radius:8px;
  overflow-x:auto;margin:0 0 16px;
}
#article pre code{background:none;padding:0;color:inherit}
#article table{width:100%;border-collapse:collapse;margin:0 0 16px;font-size:13px;font-family:var(--sans)}
#article th,#article td{border:1px solid var(--line);padding:8px 12px;text-align:left}
#article th{background:var(--panel);font-weight:700}
#article img{max-width:100%;height:auto;border-radius:6px;margin:10px 0}
#article a{color:var(--accent);border-bottom:1px solid rgba(184,150,62,.3)}
#article a:hover{border-bottom-color:var(--accent)}
#article hr{border:none;border-top:1px solid var(--line);margin:24px 0}
#article strong{font-weight:700}
#article .fnref{
  font-size:11px;color:var(--accent);cursor:pointer;font-weight:700;
  padding:0 2px;
}
#article .footnotes{
  margin-top:28px;padding-top:18px;border-top:1px solid var(--line);
  font-size:13px;color:var(--ink2);font-family:var(--sans);
}
#article .footnotes li{margin:6px 0}
#article mark{background:var(--hl);padding:0 2px;border-radius:2px}
.hl-yellow{background:var(--hl);border-radius:2px;box-shadow:inset 0 -2px 0 rgba(184,150,62,.3)}
.hl-blue{background:var(--hl2);border-radius:2px}
.hl-underline{border-bottom:2px solid #3f6212;text-decoration:none}

/* 阅读侧栏 */
#rpanel{
  position:sticky;top:65px;
  border:1px solid var(--line);background:var(--panel);
  max-height:calc(100vh - 85px);overflow-y:auto;
}
.rp-tabs{
  display:flex;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--panel);z-index:2;
}
.rp-tab{
  flex:1;padding:11px 6px;font-size:12px;font-weight:600;color:var(--ink3);
  border-bottom:2px solid transparent;transition:all .12s;text-align:center;
}
.rp-tab:hover{color:var(--ink)}
.rp-tab.active{color:var(--ink);border-bottom-color:var(--ink)}
.rp-tab .cnt{
  display:inline-block;min-width:18px;height:18px;line-height:18px;
  background:var(--line2);border-radius:9px;font-size:10px;margin-left:3px;
}
.rp-tab.active .cnt{background:var(--ink);color:#fff}
.tabpane{display:none;padding:16px 18px}
.tabpane.active{display:block}

/* 目录 */
#tab-toc a{display:block;padding:4px 0;font-size:13px;color:var(--ink2);border-bottom:none}
#tab-toc a:hover{color:var(--accent)}
#tab-toc .toc-h2{padding-left:0;font-weight:600;color:var(--ink)}
#tab-toc .toc-h3{padding-left:14px;font-size:12.5px}
#tab-toc .toc-h4{padding-left:28px;font-size:12px}
.toc-empty{font-size:13px;color:var(--ink3);padding:20px 0;text-align:center}

/* 笔记面板 */
.note-sec{margin-bottom:18px}
.note-sec h4{
  font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
  color:var(--ink3);margin-bottom:10px;
}
.note-item{
  padding:10px 12px;background:var(--bg);border-radius:6px;margin-bottom:8px;font-size:13px;
}
.note-item .sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:middle}
.note-item .sw.yellow{background:var(--hl)}
.note-item .sw.blue{background:var(--hl2)}
.note-item .qt{color:var(--ink2);font-size:12.5px;display:block;margin-bottom:4px}
.note-item .nt-text{color:var(--ink);font-size:13px;display:block;margin-top:4px;padding-top:6px;border-top:1px dashed var(--line)}
.note-item .nt-actions{margin-top:6px;display:flex;gap:8px}
.note-item .nt-del{font-size:11px;color:#b91c1c;cursor:pointer}
.note-item .nt-jump{font-size:11px;color:var(--accent);cursor:pointer}
/* 划线高亮 */
.hl-item{display:flex;align-items:flex-start;gap:8px;padding:8px 10px;background:var(--bg);border-radius:6px;margin-bottom:6px;font-size:12.5px}
.hl-item .sw{width:10px;height:10px;border-radius:2px;margin-top:5px;flex:0 0 10px}
.hl-item .sw.yellow{background:var(--hl)}
.hl-item .sw.blue{background:var(--hl2)}
.hl-item .sw.underline{background:#15803d}
.hl-item .qt{flex:1;color:var(--ink);line-height:1.6}
.hl-item .qt::before{content:"\201C";color:var(--accent)}
.hl-item .qt::after{content:"\201D";color:var(--accent)}

/* 笔记条目 */
.nt-item{display:flex;align-items:flex-start;gap:6px;padding:10px 12px;background:var(--bg);border-radius:6px;margin-bottom:8px;font-size:13px}
.nt-item .qt{color:var(--ink2);font-size:12px;border-left:2px solid var(--line);padding-left:8px;margin-bottom:4px;line-height:1.6}
.nt-item .body{color:var(--ink);line-height:1.7;white-space:pre-wrap}
.nt-tag{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.5px;padding:2px 8px;border-radius:10px;margin-bottom:5px}
.nt-tag-ai{background:#e8eef8;color:#3b5998}
.nt-tag-bg{background:#eef2e6;color:#5a7a2a}
.x-btn,.edit-btn{flex:0 0 auto;color:var(--ink3);padding:2px 6px;border-radius:5px;font-size:13px;cursor:pointer;background:none;border:none}
.x-btn:hover{color:#b91c1c;background:#fde8e8}
.edit-btn:hover{color:var(--accent);background:#f5f0e4}
.note-sec h4{display:flex;align-items:center;justify-content:space-between}
.note-clear-btn{font-size:10.5px;font-weight:400;letter-spacing:0;color:var(--ink3);border:1px solid var(--line);
  border-radius:5px;padding:2px 8px;background:var(--panel);cursor:pointer;text-transform:none}
.note-clear-btn:hover{color:#b91c1c;border-color:#e8c4c4;background:#fde8e8}

/* AI 保存按钮 */
.ai-note-btn{margin-top:8px;font-size:11.5px;color:var(--accent);border:1px solid var(--line);
  border-radius:14px;padding:3px 12px;background:var(--panel);cursor:pointer;white-space:nowrap}
.ai-note-btn:hover{border-color:var(--accent);background:var(--bg)}
.ai-note-btn.saved{color:#5a7a2a;border-color:#c5d4a8;background:#f0f4e8}
.ai-note-btn.saved:hover{background:#e6edd8}

/* 背景解释保存按钮 */
.bg-note-btn{margin-top:8px;font-size:11.5px;color:var(--accent);border:1px solid var(--line);
  border-radius:14px;padding:3px 12px;background:var(--panel);cursor:pointer;white-space:nowrap}
.bg-note-btn:hover{border-color:var(--accent);background:var(--bg)}
.bg-note-btn.saved{color:#5a7a2a;border-color:#c5d4a8;background:#f0f4e8}
.bg-note-btn.saved:hover{background:#e6edd8}

/* 已保存背景解释列表 */
.bg-saved-item{display:flex;align-items:center;gap:7px;padding:5px 8px;border-radius:5px;font-size:12px;color:var(--ink2);width:100%}
.bg-saved-item:hover{background:var(--bg)}
.bg-saved-item .bg-dot{width:6px;height:6px;border-radius:50%;background:var(--accent);flex:0 0 6px}
.bg-saved-label{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;cursor:pointer}
.bg-saved-del{flex:0 0 auto;color:var(--ink3);padding:1px 5px;border-radius:4px;font-size:12px;cursor:pointer;background:none;border:none}
.bg-saved-del:hover{color:#b91c1c;background:#fde8e8}

/* 背景解释条目（旧版兼容） */
.bg-item{border:1px solid var(--line);border-radius:7px;padding:10px 12px;margin-bottom:8px;background:var(--bg);font-size:13px}
.bg-item-term{font-weight:700;color:var(--accent);font-size:13px;margin-bottom:5px}
.bg-item-body{color:var(--ink);line-height:1.7;font-size:12.5px}
.bg-item-actions{margin-top:8px;display:flex;gap:8px}
.bg-item-qa{margin-top:8px;font-size:12px;color:var(--ink2)}
.bg-qa-user,.bg-qa-assistant{padding:4px 0}
#articleNote{
  width:100%;min-height:80px;padding:10px 12px;border:1px solid var(--line);
  border-radius:7px;font-size:13px;outline:none;resize:vertical;background:var(--bg);
  font-family:var(--sans);
}
#articleNote:focus{border-color:var(--accent)}
.note-saved{font-size:11px;color:#3f6212;margin-top:5px}

/* AI 面板 */
.ai-welcome{font-size:13px;color:var(--ink2);line-height:1.7;padding:10px 0}
.ai-msgs{max-height:380px;overflow-y:auto;margin-bottom:12px;display:flex;flex-direction:column;gap:10px}
.ai-msg{max-width:92%;padding:9px 13px;border-radius:12px;font-size:13.5px;line-height:1.75;word-break:break-word}
.ai-msg.user{align-self:flex-end;background:var(--ink);color:#fff;border-bottom-right-radius:4px}
.ai-msg.assistant{align-self:flex-start;background:var(--bg);border-bottom-left-radius:4px}
.ai-msg.err{align-self:flex-start;background:#fdecec;color:#9f1239;font-size:12.5px;border:1px solid #f5c2c2}
.ai-msg .qref{display:block;font-size:11.5px;color:var(--ink3);margin-bottom:5px;border-left:2px solid var(--line);padding-left:7px}
.ai-msg p{margin:.4em 0}
.ai-msg ul,.ai-msg ol{margin-left:1.3em}
.ai-msg code{font-size:12px;background:#e6dfd0;padding:1px 5px;border-radius:4px}
.ai-chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}
.ai-chip{
  font-size:11.5px;padding:4px 10px;border:1px solid var(--line);border-radius:20px;
  background:var(--panel);color:var(--ink2);cursor:pointer;
}
.ai-chip:hover{border-color:var(--accent);color:var(--accent)}
.ai-status{font-size:12px;color:var(--ink3);margin-bottom:8px;min-height:18px}
.ai-input{display:flex;gap:8px}
.ai-input textarea{
  flex:1;padding:9px 12px;border:1px solid var(--line);border-radius:7px;
  font-size:13px;outline:none;resize:vertical;min-height:38px;max-height:120px;background:var(--bg);
}
.ai-input textarea:focus{border-color:var(--accent)}
.ai-input button{
  padding:9px 18px;background:var(--ink);color:#fff;border-radius:7px;
  font-size:13px;font-weight:600;white-space:nowrap;
}
.ai-input button:hover{background:#333}
.ai-input button:disabled{opacity:.5;cursor:not-allowed}

/* 背景解释面板 */
.bg-term-row{display:flex;gap:6px;margin-bottom:12px;align-items:center}
.bg-term-row label{font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--ink3);white-space:nowrap}
.bg-term-row input{
  flex:1;padding:7px 10px;border:1px solid var(--line);border-radius:6px;
  font-size:13px;outline:none;background:var(--bg);
}
.bg-term-row input:focus{border-color:var(--accent)}
.bg-term-row button{
  padding:7px 14px;background:var(--ink);color:#fff;border-radius:6px;font-size:12px;font-weight:600;
}
.bg-term-row button:hover{background:#333}
.bg-msgs{max-height:340px;overflow-y:auto;margin-bottom:12px;display:flex;flex-direction:column;gap:10px}
.bg-msg{max-width:96%;padding:10px 13px;border-radius:12px;font-size:13.5px;line-height:1.75;word-break:break-word}
.bg-msg.term{align-self:stretch;max-width:100%;background:var(--bg);border:1px solid var(--line);
  border-radius:8px;font-weight:600;color:var(--accent);text-align:center}
.bg-msg.assistant{align-self:flex-start;background:var(--bg);border-bottom-left-radius:4px}
.bg-msg.user{align-self:flex-end;background:var(--ink);color:#fff;border-bottom-right-radius:4px}
.bg-msg.err{align-self:flex-start;background:#fdecec;color:#9f1239;font-size:12.5px;border:1px solid #f5c2c2}
.bg-msg p{margin:.4em 0}
.bg-msg ul,.bg-msg ol{margin-left:1.3em}
.bg-msg code{font-size:12px;background:#e6dfd0;padding:1px 5px;border-radius:4px}
.bg-saved{margin-top:14px;padding-top:14px;border-top:1px solid var(--line)}
.bg-saved h4{font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--ink3);margin-bottom:8px}
.bg-status{font-size:12px;color:var(--ink3);margin-bottom:8px;min-height:18px}
.bg-input{display:flex;gap:8px}
.bg-input textarea{
  flex:1;padding:8px 12px;border:1px solid var(--line);border-radius:7px;
  font-size:13px;outline:none;resize:vertical;min-height:38px;background:var(--bg);
}
.bg-input button{padding:8px 16px;background:var(--ink);color:#fff;border-radius:7px;font-size:13px;font-weight:600}
.bg-input button:disabled{opacity:.5;cursor:not-allowed}
.bg-welcome{padding:8px 4px;color:var(--ink2);font-size:13px;line-height:1.9}
.bg-welcome .bg-tip{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin-top:12px;font-size:12.5px;line-height:1.8}

.reader-foot{
  display:flex;justify-content:space-between;align-items:center;
  padding:20px 0;margin-top:32px;border-top:1px solid var(--line);
}

/* ==================== 选中工具栏 ==================== */
#selToolbar{
  position:absolute;z-index:200;display:flex;gap:2px;
  background:var(--sidebar-bg);border-radius:8px;padding:4px;
  box-shadow:0 4px 20px rgba(0,0,0,.18);
}
#selToolbar button{
  padding:6px 10px;font-size:12px;color:var(--sidebar-text);border-radius:5px;
  white-space:nowrap;
}
#selToolbar button:hover{background:var(--sidebar-hover)}
#selToolbar .sep{width:1px;background:#3a3935;margin:4px 2px}

/* ==================== 弹窗 ==================== */
#modalBackdrop,#settingsModal{
  position:fixed;inset:0;z-index:300;
  background:rgba(28,28,28,.5);backdrop-filter:blur(3px);
  display:flex;align-items:center;justify-content:center;padding:20px;
}
.modal{
  background:var(--panel);border-radius:12px;padding:28px;
  width:100%;max-width:480px;max-height:90vh;overflow-y:auto;
  box-shadow:0 20px 60px rgba(0,0,0,.2);
}
.modal h3{font:700 19px/1.3 var(--serif);margin-bottom:18px;color:var(--ink)}
.field{margin-bottom:16px}
.field label{display:block;font-size:12px;font-weight:600;color:var(--ink2);margin-bottom:6px}
.field input,.field textarea{
  width:100%;padding:9px 12px;border:1px solid var(--line);border-radius:7px;
  font-size:14px;outline:none;background:var(--bg);
}
.field input:focus,.field textarea:focus{border-color:var(--accent)}
.quote-box{
  background:var(--bg);border-left:3px solid var(--accent);padding:10px 14px;
  font-size:13px;color:var(--ink2);margin-bottom:16px;border-radius:0 6px 6px 0;
}
.hint{font-size:12px;color:var(--ink3);margin-top:6px}
.modal-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:20px}
.btn{
  padding:9px 20px;border-radius:7px;font-size:13px;font-weight:600;cursor:pointer;
  transition:all .12s;
}
.btn.ghost{background:none;border:1px solid var(--line);color:var(--ink2)}
.btn.ghost:hover{border-color:var(--ink);color:var(--ink)}
.btn.primary{background:var(--ink);border:1px solid var(--ink);color:#fff}
.btn.primary:hover{background:#333}

/* ==================== 索引纵览页 ==================== */
#idxView{min-height:100vh;background:var(--bg)}
.iv-hero{
  background:var(--sidebar-bg);color:var(--sidebar-text);
  padding:64px 32px 48px;text-align:center;
}
.iv-hero-inner{max-width:800px;margin:0 auto}
.iv-eyebrow{
  font-size:11px;font-weight:600;letter-spacing:2.5px;text-transform:uppercase;
  color:var(--sidebar-muted);margin-bottom:18px;
}
.iv-hero h1{font:700 42px/1.15 var(--serif);margin-bottom:14px}
.iv-hero h1 em{font-style:normal;color:var(--accent)}
.iv-hero-sub{font-size:14.5px;color:#b0ada5;line-height:1.7;max-width:600px;margin:0 auto 28px}
.iv-stats{display:flex;justify-content:center;gap:0;border:1px solid #33322f}
.iv-stat{padding:18px 32px;text-align:center;border-right:1px solid #33322f}
.iv-stat:last-child{border-right:none}
.iv-stat-num{font:700 28px/1 var(--serif);color:var(--sidebar-text)}
.iv-stat-label{font-size:10px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:var(--sidebar-muted);margin-top:6px}

.iv-nav{
  position:sticky;top:0;z-index:40;background:rgba(245,244,240,.92);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--line);
}
.iv-nav-inner{
  max-width:1100px;margin:0 auto;padding:0 32px;
  display:flex;align-items:center;gap:4px;overflow-x:auto;
}
.iv-nav-brand{
  font:700 15px var(--serif);color:var(--ink);padding:14px 16px 14px 0;
  white-space:nowrap;border-right:1px solid var(--line);margin-right:8px;cursor:pointer;
  background:none;border-top:none;border-left:none;border-bottom:none;
  display:inline-flex;align-items:center;gap:6px;
}
.iv-nav-brand:hover{color:var(--accent)}
.iv-tab{
  padding:14px 16px;font-size:13px;font-weight:600;color:var(--ink3);
  border-bottom:2px solid transparent;white-space:nowrap;transition:all .12s;
}
.iv-tab:hover{color:var(--ink)}
.iv-tab.active{color:var(--ink);border-bottom-color:var(--ink)}

.iv-filter-bar{
  max-width:1100px;margin:0 auto;padding:14px 32px;
  display:flex;align-items:center;gap:10px;flex-wrap:wrap;
  border-bottom:1px solid var(--line);
}
.iv-filter-label{font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--ink3)}
.iv-filter-group{display:flex;gap:4px;flex-wrap:wrap}
.iv-filter-div{width:1px;height:20px;background:var(--line);margin:0 6px}
.iv-filter-btn{
  padding:4px 12px;font-size:12px;border:1px solid var(--line);border-radius:20px;
  background:var(--panel);color:var(--ink2);cursor:pointer;
}
.iv-filter-btn:hover{border-color:var(--ink)}
.iv-filter-btn.active{background:var(--ink);border-color:var(--ink);color:#fff}

.iv-pane{max-width:1100px;margin:0 auto;padding:0 32px 60px;display:none}
.iv-pane.active{display:block}

/* 索引页通用 section */
.iv-section{max-width:1100px;margin:0 auto;padding:32px 32px 12px}
.iv-sec-head{display:flex;align-items:baseline;gap:12px;margin-bottom:4px;flex-wrap:wrap}
.iv-sec-title{font:700 22px/1.3 var(--serif);color:var(--ink)}
.iv-sec-meta{font-size:13px;color:var(--ink3)}
.iv-sec-desc{font-size:13.5px;color:var(--ink2);margin-bottom:18px;padding-bottom:16px;border-bottom:1px solid var(--line);line-height:1.7}

/* 年度信件条目 */
.iv-letter{display:grid;grid-template-columns:72px 1fr;gap:20px;padding:22px 0;border-bottom:1px solid var(--line);transition:background .12s}
.iv-letter:hover{background:rgba(0,0,0,.015);margin:0 -16px;padding-left:16px;padding-right:16px}
.iv-letter-year{font:700 26px/1 var(--serif);color:var(--ink);text-align:right;padding-top:3px}
.iv-letter-body{min-width:0}
.iv-letter-meta{display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap}
.iv-series-badge{font-size:10px;font-weight:700;letter-spacing:.5px;padding:2px 8px;border-radius:3px}
.iv-series-badge.partnership{background:rgba(107,91,149,.1);color:#6b5b95}
.iv-series-badge.berkshire{background:rgba(30,79,158,.1);color:#1e4f9e}
.iv-letter-author{font-size:12.5px;color:var(--ink3)}
.iv-letter-title{font:700 16px/1.4 var(--serif);margin-bottom:6px}
.iv-letter-title a{color:var(--ink)}
.iv-letter-title a:hover{color:var(--accent)}
.iv-letter-summary{font-size:13.5px;color:var(--ink2);line-height:1.75;margin-bottom:9px}
.iv-letter-tags{display:flex;gap:5px;flex-wrap:wrap;align-items:center}
.iv-letter-ctx{font-size:12px;color:var(--ink3);margin-top:6px;font-style:italic}
.iv-letter-link{
  display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:700;
  letter-spacing:1px;text-transform:uppercase;color:var(--accent);margin-left:auto;transition:gap .15s;
}
.iv-letter-link:hover{gap:7px}

/* 标签 */
.iv-tag{font-size:11px;padding:2px 8px;border-radius:3px;background:var(--line2);color:var(--ink2);letter-spacing:.3px}
.iv-tag.theme{background:rgba(184,150,62,.1);color:var(--accent)}
.iv-tag.ev-crisis{background:rgba(192,57,43,.08);color:#c0392b;font-weight:600}
.iv-tag.ev-bubble{background:rgba(211,84,0,.08);color:#d35400;font-weight:600}
.iv-tag.ev-inflation{background:rgba(184,134,11,.08);color:#b8860b;font-weight:600}
.iv-tag.ev-war{background:rgba(93,78,55,.1);color:#5d4e37;font-weight:600}
.iv-tag.ev-pandemic{background:rgba(41,128,185,.08);color:#2980b9;font-weight:600}
.iv-tag.ev-normal{background:rgba(39,99,42,.06);color:#27632a;font-weight:600}
.iv-year-tag{font-size:11px;padding:2px 8px;border-radius:3px;background:var(--line2);color:var(--ink2)}

/* 卡片（主题/行业/事件/方法） */
.iv-card{padding:22px 0;border-bottom:1px solid var(--line)}
.iv-card:hover{background:rgba(0,0,0,.015);margin:0 -16px;padding-left:16px;padding-right:16px;transition:background .12s}
.iv-card-head{display:flex;align-items:baseline;gap:10px;margin-bottom:9px;flex-wrap:wrap}
.iv-card-num{font:700 13px/1 var(--serif);color:var(--accent);min-width:26px}
.iv-card-title{font:700 17px/1.4 var(--serif);color:var(--ink)}
.iv-card-sub{font-size:12.5px;color:var(--ink3)}
.iv-card-body{font-size:13.5px;color:var(--ink2);line-height:1.75;margin-bottom:9px}
.iv-card-label{font-size:10.5px;font-weight:700;color:var(--ink3);letter-spacing:1px;text-transform:uppercase;margin-top:9px;margin-bottom:4px}
.iv-card-text{font-size:13px;color:var(--ink2);line-height:1.7}
.iv-card-tags{display:flex;gap:5px;flex-wrap:wrap;margin-top:7px}
.iv-card-row{display:grid;grid-template-columns:100px 1fr;gap:14px;margin-top:7px}
.iv-card-row-label{font-size:12px;font-weight:700;color:var(--ink3);letter-spacing:.3px;padding-top:2px}
.iv-card-row-value{font-size:13px;color:var(--ink2);line-height:1.7}

/* 事件时期标签 */
.iv-event-period{display:inline-block;font-size:12px;font-weight:700;padding:2px 10px;border-radius:3px;margin-bottom:7px}
.iv-period-crisis{background:rgba(192,57,43,.08);color:#c0392b}
.iv-period-bubble{background:rgba(211,84,0,.08);color:#d35400}
.iv-period-inflation{background:rgba(184,134,11,.08);color:#b8860b}
.iv-period-war{background:rgba(93,78,55,.1);color:#5d4e37}
.iv-period-pandemic{background:rgba(41,128,185,.08);color:#2980b9}
.iv-period-normal{background:rgba(39,99,42,.06);color:#27632a}

/* 选股方法 */
.iv-method-era{font:700 14px/1 var(--serif);color:var(--accent);margin-bottom:4px}
.iv-method-method{font-size:13.5px;font-weight:700;color:var(--ink);margin-bottom:7px}

.iv-empty{text-align:center;padding:44px 24px;color:var(--ink3)}

.iv-footer{
  max-width:1100px;margin:0 auto;padding:28px 32px;
  border-top:1px solid var(--line);font-size:12px;color:var(--ink3);line-height:1.8;text-align:center;
}
.iv-footer a{color:var(--accent) !important}

/* ==================== Toast ==================== */
#toast{
  position:fixed;bottom:28px;left:50%;transform:translateX(-50%) translateY(20px);
  background:var(--sidebar-bg);color:var(--sidebar-text);
  padding:11px 22px;border-radius:8px;font-size:13px;
  opacity:0;pointer-events:none;transition:all .25s;z-index:400;
  box-shadow:0 6px 24px rgba(0,0,0,.2);
}
#toast.show{opacity:1;transform:translateX(-50%) translateY(0)}

/* ==================== 响应式 ==================== */
#sidebarBackdrop{display:none}
@media (max-width:960px){
  #sidebar{
    transform:translateX(-100%);transition:transform .25s;
    width:280px;flex:0 0 280px;
  }
  #sidebar.open{transform:translateX(0)}
  #sidebarBackdrop{
    position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:55;
  }
  #sidebarBackdrop.show{display:block}
  #mainCol{margin-left:0}
  #progress{left:0}
  #menuBtn{
    display:inline-flex;align-items:center;justify-content:center;
    width:34px;height:34px;border:1px solid var(--line);border-radius:7px;
    background:var(--panel);font-size:16px;
  }
  #main{padding:0 18px 40px}
  #topbar{padding:10px 18px}
  .home-hero{grid-template-columns:1fr;gap:24px;padding:36px 0 28px}
  .home-hero h1{font-size:36px}
  .hh-stats{grid-template-columns:repeat(2,1fr)}
  .hh-stats>div:nth-child(2){border-right:none}
  .feature-grid{grid-template-columns:1fr}
  .home-grid{grid-template-columns:1fr 1fr}
  .reader-body{grid-template-columns:1fr}
  #rpanel{position:static;max-height:none}
  .reader-top{flex-direction:column}
  .iv-hero h1{font-size:30px}
  .iv-stats{flex-wrap:wrap}
  .iv-stat{flex:1 1 40%}
  .iv-year-body{grid-template-columns:1fr}
  .iv-letter{grid-template-columns:52px 1fr;gap:12px}
  .iv-letter-year{font-size:20px}
  .iv-card-row{grid-template-columns:1fr;gap:3px}
  .iv-stats{gap:18px}
  .iv-stat{padding:14px 20px}
  .iv-stat-num{font-size:22px}
  .iv-section{padding:24px 18px 8px}
  .iv-pane{padding:0 18px 40px}
  .iv-filter-bar{padding:12px 18px}
  .iv-footer{padding:24px 18px}
  .talk-banner{flex-direction:column;align-items:flex-start;gap:14px}
}
@media (max-width:600px){
  .home-grid{grid-template-columns:1fr}
  .home-row{grid-template-columns:56px 1fr}
  .hr-why{display:none}
  .hh-stats b{font-size:24px}
}
"""

# ============================================================ HTML 模板
V2_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="巴菲特致股东信知识库 · chian.io 风格 · 分类/搜索/阅读/笔记/划线/LLM 讨论">
<title>巴菲特致股东信 · 知识库 1956–2025</title>
<style>
__CSS__
</style>
</head>
<body>
<div id="layout">
  <aside id="sidebar">
    <div class="sb-brand" id="brandBtn" title="回到主页">
      <div class="sb-brand-title">巴菲特致股东信</div>
      <div class="sb-brand-sub">知识库 · 1956–2025</div>
    </div>
    <div class="sb-search">
      <input id="q" type="search" placeholder="搜索信件、概念、公司、人物…" autocomplete="off">
      <span id="qCount"></span>
    </div>
    <nav class="sb-nav">
      <button class="sb-nav-item active" id="navHome"><span class="ico">&#8962;</span> 知识库首页</button>
      <button class="sb-nav-item" id="navIndex"><span class="ico">&#9776;</span> 索引纵览</button>
    </nav>
    <div class="sb-sec">
      <div class="sb-title">原始文献</div>
      <div id="sbCats"></div>
    </div>
    <div class="sb-sec">
      <div class="sb-title">分类索引 <span class="sb-title-range" id="idxRange"></span></div>
      <div id="sbIdx"></div>
    </div>
    <div class="sb-sec">
      <div class="sb-title">年代</div>
      <div id="sbDecades"></div>
    </div>
    <div class="sb-sec">
      <div class="sb-title">主题标签</div>
      <div class="tag-cloud" id="sbTags"></div>
    </div>
    <div class="sb-sec">
      <div class="sb-title">状态</div>
      <label class="sb-check"><input type="checkbox" id="sbFav"> &#9733; 仅看收藏</label>
      <label class="sb-check"><input type="checkbox" id="sbNoted"> &#9998; 有笔记/高亮</label>
    </div>
    <button class="sb-talk" id="navTalk">
      <div class="sb-talk-title">与巴菲特对话 <span class="sb-talk-beta">AI</span></div>
      <div class="sb-talk-desc">基于 60+ 年股东信的 AI 讨论</div>
    </button>
    <div class="sb-foot">
      <div id="sbFootInfo"></div>
      <a href="巴菲特投资智慧.html" class="sb-switch">切换经典版 &rarr;</a>
    </div>
  </aside>

  <div id="mainCol">
    <header id="topbar">
      <button class="tbtn" id="menuBtn" title="筛选面板">&#9776;</button>
      <div class="top-actions">
        <select class="tbtn" id="sortSel" title="排序">
          <option value="year-asc">时间 &uarr;</option>
          <option value="year-desc">时间 &darr;</option>
          <option value="title">标题</option>
          <option value="cat">分类</option>
          <option value="len">篇幅</option>
          <option value="fav">收藏优先</option>
        </select>
        <select class="tbtn" id="groupSel" title="分组">
          <option value="none">不分组</option>
          <option value="cat">按分类分组</option>
          <option value="decade">按年代分组</option>
          <option value="tag">按主题分组</option>
        </select>
        <select class="tbtn" id="viewSel" title="视图">
          <option value="grid">卡片</option>
          <option value="rows">列表</option>
        </select>
        <button class="tbtn" id="indexBtn" title="编辑风索引纵览">&#9776; 索引</button>
        <button class="tbtn" id="notesExport" title="导出全部笔记">&#8681; 导出笔记</button>
        <button class="tbtn" id="settingsBtn" title="LLM 设置">&#9881; 设置</button>
      </div>
    </header>
    <div id="sidebarBackdrop"></div>
    <main id="main">
      <div id="home" hidden></div>
      <div id="library" hidden>
        <div id="libHead">
          <span id="libTitle">全部文章</span>
          <span id="libCount"></span>
        </div>
        <div id="idxBanner"></div>
        <div id="libList"></div>
      </div>
      <div id="reader" hidden>
        <div id="progress"></div>
        <div class="reader-top">
          <button class="tbtn" id="backBtn">&larr; 返回列表</button>
          <div class="reader-title">
            <h1 id="rTitle"></h1>
            <div class="r-meta" id="rMeta"></div>
            <div class="r-tags" id="rTags"></div>
            <div class="r-idx" id="rIdxLine"></div>
          </div>
          <div class="r-actions">
            <button class="tbtn" id="rFav" title="收藏">&#9734;</button>
            <button class="tbtn" id="rPrev">&larr; 上一篇</button>
            <button class="tbtn" id="rNext">下一篇 &rarr;</button>
          </div>
        </div>
        <div class="reader-body">
          <article id="article"></article>
          <aside id="rpanel">
            <div class="rp-tabs">
              <button class="rp-tab active" data-tab="toc">目录</button>
              <button class="rp-tab" data-tab="notes">笔记<span class="cnt" id="notesCnt"></span></button>
              <button class="rp-tab" data-tab="ai">AI 讨论</button>
              <button class="rp-tab" data-tab="bg">背景解释</button>
            </div>
            <div class="tabpane active" id="tab-toc"></div>
            <div class="tabpane" id="tab-notes">
              <div class="note-sec"><h4>划线高亮</h4><div id="ntHighlights"></div></div>
              <div class="note-sec"><h4>笔记</h4><div id="ntNotes"></div></div>
              <div class="note-sec"><h4>背景解释</h4><div id="ntBg"></div></div>
              <div class="note-sec"><h4>文章笔记（自动保存）<button class="note-clear-btn" id="clearArticleNote" title="清空文章笔记">清空</button></h4>
                <textarea id="articleNote" placeholder="记录你对这篇文章的理解、与 A 股实践的关联…"></textarea>
                <div class="note-saved" id="noteSaved"></div>
              </div>
            </div>
            <div class="tabpane" id="tab-ai">
              <div class="ai-msgs" id="aiMsgs"></div>
              <div class="ai-chips" id="aiChips"></div>
              <div class="ai-status" id="aiStatus"></div>
              <div class="ai-input" id="aiInput" style="display:none">
                <textarea id="aiInputBox" rows="1" placeholder="问 AI：这段思想如何应用到我的股票投资？"></textarea>
                <button id="aiSend">发送</button>
              </div>
            </div>
            <div class="tabpane" id="tab-bg">
              <div class="bg-head">
                <div class="bg-term-row">
                  <label>词语</label>
                  <input id="bgTermInput" type="text" placeholder="输入或选中词语后点「解释」">
                  <button id="bgExplainBtn">解释</button>
                </div>
              </div>
              <div class="bg-msgs" id="bgMsgs"></div>
              <div class="bg-saved" id="bgSaved" hidden>
                <h4>&#128218; 本文已保存的背景解释</h4>
                <div id="bgSavedList"></div>
              </div>
              <div class="bg-status" id="bgStatus"></div>
              <div class="bg-input" id="bgInput" style="display:none">
                <textarea id="bgInputBox" rows="1" placeholder="就这个解释继续追问…（Enter 发送）"></textarea>
                <button id="bgSend">发送</button>
              </div>
            </div>
          </aside>
        </div>
        <div class="reader-foot">
          <span class="tbtn" id="rNavInfo" style="border:none;background:none"></span>
          <span style="font-size:12px;color:var(--ink3)" id="rFootInfo">选中文字可高亮 / 下划线 / 背景解释 / 记笔记</span>
        </div>
      </div>
    </main>
  </div>
</div>

<div id="selToolbar" hidden>
  <button id="hlYellow" title="黄色高亮">&#128992; 高亮</button>
  <button id="hlBlue" title="蓝色高亮">&#128309; 高亮</button>
  <button id="hlUnderline" title="绿色下划线">&#128994; 划线</button>
  <span class="sep"></span>
  <button id="hlBg" title="用 AI 解释选中词语的金融概念与时代背景">&#128269; 背景解释</button>
  <span class="sep"></span>
  <button id="hlNote" title="基于选中文字写笔记">&#9998; 笔记</button>
  <button id="hlCopy" title="复制选中文字">&#10697; 复制</button>
</div>

<div id="modalBackdrop" hidden>
  <div class="modal">
    <h3 id="nmTitle">新建笔记</h3>
    <div class="quote-box" id="nmQuote"></div>
    <div class="field">
      <textarea id="nmText" rows="5" placeholder="写下你的想法…（会随文章保存，可导出）"></textarea>
    </div>
    <div class="modal-actions">
      <button class="btn ghost" id="nmCancel">取消</button>
      <button class="btn primary" id="nmSave">保存笔记</button>
    </div>
  </div>
</div>

<div id="settingsModal" hidden>
  <div class="modal">
    <h3>&#9881; LLM 讨论设置</h3>
    <div class="field">
      <label>API Base（OpenAI 兼容）</label>
      <input type="text" id="setBase" placeholder="https://api.deepseek.com/v1">
    </div>
    <div class="field">
      <label>API Key</label>
      <input type="password" id="setKey" placeholder="sk-...">
    </div>
    <div class="field">
      <label>模型</label>
      <input type="text" id="setModel" placeholder="deepseek-v4-flash">
    </div>
    <div class="hint" id="setHint"></div>
    <div class="hint" style="color:#3f6212" id="setTestResult"></div>
    <div class="modal-actions">
      <button class="btn ghost" id="setCancel">取消</button>
      <button class="btn ghost" id="setTest">测试连接</button>
      <button class="btn primary" id="setSave">保存</button>
    </div>
  </div>
</div>

<div id="idxView" hidden>
  <header class="iv-hero">
    <div class="iv-hero-inner">
      <div class="iv-eyebrow">Warren Buffett &middot; 1956&ndash;2025</div>
      <h1>巴菲特致股东信<em>分类索引</em></h1>
      <p class="iv-hero-sub">按年度、主题、行业、事件时期、选股方法五个维度，系统梳理巴菲特投资思想的演进脉络。</p>
      <div class="iv-stats" id="ivStats"></div>
    </div>
  </header>
  <nav class="iv-nav">
    <div class="iv-nav-inner">
      <button class="iv-nav-brand" id="ivBack" title="返回主页">&larr; 巴菲特致股东信</button>
      <button class="iv-tab active" data-ivtab="letters">&#128197; 年度信件</button>
      <button class="iv-tab" data-ivtab="themes">&#127991;&#65039; 主题分类</button>
      <button class="iv-tab" data-ivtab="industries">&#127981; 行业分类</button>
      <button class="iv-tab" data-ivtab="events">&#127744; 事件时期</button>
      <button class="iv-tab" data-ivtab="methods">&#129517; 选股方法</button>
    </div>
  </nav>
  <div class="iv-filter-bar" id="ivFilterBar"></div>
  <div id="ivLetters" class="iv-pane active"></div>
  <div id="ivThemes" class="iv-pane"></div>
  <div id="ivIndustries" class="iv-pane"></div>
  <div id="ivEvents" class="iv-pane"></div>
  <div id="ivMethods" class="iv-pane"></div>
  <footer class="iv-footer" id="ivFooter"></footer>
</div>

<div id="toast"></div>

<script>
window.BUFFETT_DATA = __DATA__;
</script>
<script src="llm-config.js" onerror="window.__noLlmCfg=1"></script>
<script>
__JS__
</script>
</body>
</html>
"""

# ============================================================ JS 补丁
# 在原 APP_JS 之后执行，覆盖主页渲染、侧边栏导航等
V2_JS_PATCH = r"""
/* ==================== v2 补丁：chian.io 风格适配 ==================== */

/* ---- 侧边栏导航 ---- */
(function(){
  const navHome = document.getElementById('navHome');
  const navIndex = document.getElementById('navIndex');
  const navTalk = document.getElementById('navTalk');
  if(navHome) navHome.onclick = ()=>{ if(location.hash!=='#/' && location.hash!=='') location.hash='#/'; else { location.hash='#/'; } };
  if(navIndex) navIndex.onclick = ()=>{ location.hash='#/index'; closeMobileSidebar(); };
  if(navTalk) navTalk.onclick = ()=>{
    const s = settings();
    if(!s.key){
      toast('请先在「设置」中配置 API Key，然后打开任意信件即可与 AI 讨论');
      document.getElementById('settingsBtn').click();
      return;
    }
    // 跳转到最新一封伯克希尔信并打开 AI 标签
    const latest = ART.filter(a=>a.catKey==='berkshire'&&a.year).sort((a,b)=>b.year-a.year)[0];
    if(latest){ location.hash='#/a/'+latest.id; setTimeout(()=>{ const t=document.querySelector('.rp-tab[data-tab="ai"]'); if(t) t.click(); },400); }
  };

  // 索引页返回按钮
  const ivBack = document.getElementById('ivBack');
  if(ivBack) ivBack.onclick = ()=>{ location.hash='#/'; };

  function closeMobileSidebar(){
    const sb=document.getElementById('sidebar'), bd=document.getElementById('sidebarBackdrop');
    if(sb) sb.classList.remove('open');
    if(bd) bd.classList.remove('show');
  }

  // 移动端：点击导航后关闭侧边栏
  document.querySelectorAll('#sidebar .sb-item, #sidebar .idx-gtitle, #sidebar .tag-chip, #sidebar .sb-check').forEach(el=>{
    el.addEventListener('click', ()=>{ if(window.innerWidth<=960) setTimeout(closeMobileSidebar,150); });
  });
})();

/* ---- 路由时更新侧边栏 active 状态 ---- */
(function(){
  function updateNavActive(){
    const navHome = document.getElementById('navHome');
    const navIndex = document.getElementById('navIndex');
    if(!navHome) return;
    const isIndex = location.hash === '#/index';
    const isHome = location.hash === '#/' || location.hash === '';
    navHome.classList.toggle('active', isHome);
    navIndex.classList.toggle('active', isIndex);
  }
  window.addEventListener('hashchange', updateNavActive);
  setTimeout(updateNavActive, 100);
})();

/* ---- 覆盖主页渲染（chian.io 风格） ---- */
renderHome = function(){
  const el = homeEl;
  const yearItems = IDX.year||[];
  const years = yearItems.map(x=>x.y).filter(Boolean);
  const yMin = years.length?Math.min.apply(null,years):DATA.yearRange[0];
  const yMax = years.length?Math.max.apply(null,years):DATA.yearRange[1];
  const nLetters = ART.filter(a=>['berkshire','partnership','special'].includes(a.catKey)).length;
  const nConcepts = ART.filter(a=>a.catKey==='concept').length;
  const nCompanies = ART.filter(a=>a.catKey==='company').length;
  const nPeople = ART.filter(a=>a.catKey==='person').length;
  const nTags = new Set();
  ART.forEach(a=>(a.tags||[]).forEach(t=>nTags.add(t)));
  const nCross = ART.reduce((s,a)=>s+(a.links?a.links.length:0),0);

  const recent = ART.filter(a=>a.catKey==='berkshire'&&a.year&&a.year>=2021).sort((a,b)=>b.year-a.year).slice(0,5);

  const tagCounts={};
  ART.forEach(a=>(a.tags||[]).forEach(t=>tagCounts[t]=(tagCounts[t]||0)+1));
  const hotTags = Object.entries(tagCounts).sort((a,b)=>b[1]-a[1]).slice(0,24);

  const last = store.get('bf_last',null);
  const lastArt = last&&BYID[last.id]?BYID[last.id]:null;

  const classics=[
    ['berkshire-1983-巴菲特致股东信','1983','商誉与所有者收益','收购标准、经济商誉、回购'],
    ['berkshire-1984-巴菲特致股东信','1984','格雷厄姆-多德都市的超级投资者','九位价值投资者业绩'],
    ['berkshire-1987-巴菲特致股东信','1987','市场先生','黑色星期一：波动是机会'],
    ['berkshire-1994-巴菲特致股东信','1994','大师级框架','理解伯克希尔哲学'],
    ['berkshire-2008-巴菲特致股东信','2008','买入美国','金融危机中的行动'],
    ['berkshire-2016-巴菲特致股东信','2016','苹果投资','能力圈扩展到科技'],
    ['berkshire-2021-巴菲特致股东信','2021','美国顺风','长期主义与反对投机'],
    ['berkshire-2023-巴菲特致股东信','2023','纪念芒格','思想伙伴关系'],
  ].filter(x=>BYID[x[0]]);

  // 四宫格
  const features = [
    ['Letters','&#9993;','原始文献','信件',nLetters+' 封信','1956–2025 合伙人信与伯克希尔股东信，全文交叉引用',{cat:'all'}],
    ['Concepts','&#9432;','投资框架','概念',nConcepts+' 个概念','内在价值、安全边际、经济护城河、所有者收益…',{cat:'concept'}],
    ['Companies','&#9758;','投资历史','公司',nCompanies+' 家公司','从喜诗糖果到苹果，追踪巴菲特投资哲学演变',{cat:'company'}],
    ['People','&#9788;','关键人物','人物',nPeople+' 位人物','导师、合伙人与经理人——塑造伯克希尔的人',{cat:'person'}],
  ];

  el.innerHTML =
    '<div class="home-hero">'+
      '<div class="hh-left">'+
        '<div class="hh-eyebrow">知识库 &middot; '+yMin+'&ndash;'+yMax+'</div>'+
        '<h1>70 年投资智慧，<br>逐封<em class="accent">解码</em>。</h1>'+
      '</div>'+
      '<div class="hh-right">'+
        '<div class="hh-sub">从 1956 年合伙人信到 2025 年伯克希尔股东信，'+ART.length+' 篇文章转化为无损、全映射的知识库。分类浏览、全文检索、阅读划线、笔记与 AI 讨论——为人类头脑与智能体而设计。</div>'+
        '<button class="hh-btn" id="heroBrowse">浏览信件 <span class="arr">&rarr;</span></button>'+
      '</div>'+
    '</div>'+
    '<div class="hh-stats">'+
      '<div><b>'+nLetters+'</b><span>信件</span></div>'+
      '<div><b>'+nConcepts+'</b><span>概念</span></div>'+
      '<div><b>'+nCompanies+'</b><span>公司</span></div>'+
      '<div><b>'+nCross+'+</b><span>交叉引用</span></div>'+
    '</div>'+

    '<div class="talk-banner">'+
      '<div class="tb-left">'+
        '<div class="tb-title">与巴菲特对话 <span class="tb-beta">AI</span></div>'+
        '<div class="tb-sub">AI &middot; 60+ 年股东信</div>'+
      '</div>'+
      '<div class="tb-desc">有投资问题？基于全部股东信内容回答，每条回答可追溯至原文。</div>'+
      '<button class="tb-btn" id="heroTalk">开始对话 &rarr;</button>'+
    '</div>'+

    '<div class="feature-grid">'+
      features.map(f=>
        '<div class="feature-card" data-go=\''+JSON.stringify(f[6])+'\'>'+
          '<div class="fc-badge">'+f[4]+'</div>'+
          '<div class="fc-icon">'+f[1]+'</div>'+
          '<div class="fc-label">'+f[2]+'</div>'+
          '<div class="fc-title">'+f[3]+'</div>'+
          '<div class="fc-desc">'+f[5]+'</div>'+
          '<div class="fc-link">浏览'+f[3]+' &rarr;</div>'+
        '</div>'
      ).join('')+
    '</div>'+

    (hotTags.length?
    '<div class="home-sec">'+
      '<div class="sec-eyebrow">核心投资概念</div>'+
      '<h2>思想框架</h2>'+
      '<div class="sec-sub">按在全部信件中出现频率排列</div>'+
      '<div class="concept-tags">'+
        hotTags.map(t=>'<button class="concept-tag" data-tag="'+esc(t[0])+'">'+esc(t[0])+'<span class="ct-count">'+t[1]+'</span></button>').join('')+
      '</div>'+
    '</div>':'')+

    '<div class="home-sec">'+
      '<div class="sec-eyebrow">最新信件</div>'+
      '<h2>来自伯克希尔的最新声音</h2>'+
      '<div class="home-list">'+
        recent.map(a=>
          '<div class="home-row" data-art="'+a.id+'">'+
            '<span class="hr-year">'+a.year+' &middot; BERKSHIRE</span>'+
            '<span class="hr-title">'+esc(a.title)+'</span>'+
            '<span class="hr-why">'+(a.tags||[]).slice(0,3).map(esc).join(' &middot; ')+'</span>'+
          '</div>'
        ).join('')+
      '</div>'+
    '</div>'+

    (classics.length?
    '<div class="home-sec">'+
      '<div class="sec-eyebrow">必读经典</div>'+
      '<h2>不可错过的八封信</h2>'+
      '<div class="home-list">'+
        classics.map(c=>
          '<div class="home-row" data-art="'+c[0]+'">'+
            '<span class="hr-year">'+c[1]+'</span>'+
            '<span class="hr-title">'+esc(c[2])+'</span>'+
            '<span class="hr-why">'+esc(c[3])+'</span>'+
          '</div>'
        ).join('')+
      '</div>'+
    '</div>':'')+

    (lastArt?
      '<div class="home-last" data-art="'+lastArt.id+'">'+
        '<span class="hl-ic">&#128214;</span>'+
        '<div><div class="hl-title">继续阅读：'+esc(lastArt.title)+'</div>'+
        '<div class="hl-time">上次读到 '+fmtAgo(last.ts||Date.now())+'</div></div>'+
        '<span class="arr">&rarr;</span>'+
      '</div>':'');

  // Hero 按钮
  const hb = document.getElementById('heroBrowse');
  if(hb) hb.onclick = ()=>goLibrary({cat:'all'});
  const ht = document.getElementById('heroTalk');
  if(ht) ht.onclick = ()=>document.getElementById('navTalk').click();
};

/* ---- 侧边栏分类项加图标 ---- */
(function(){
  const _origRenderSidebar = renderSidebar;
  const catIcons = {'全部':'&#8801;','索引':'&#8801;','合伙人信':'&#9998;','伯克希尔股东信':'&#9784;','特别信件':'&#9733;','概念':'&#9432;','公司':'&#9758;','人物':'&#9788;'};
  renderSidebar = function(){
    _origRenderSidebar();
    document.querySelectorAll('#sbCats .sb-item').forEach(item=>{
      if(item.classList.contains('has-ico')) return;
      const label = item.querySelector('span:first-child');
      if(!label) return;
      const name = label.textContent.trim();
      const ico = catIcons[name] || '&middot;';
      item.classList.add('has-ico');
      label.innerHTML = '<span class="ico">'+ico+'</span><span>'+esc(name)+'</span>';
    });
  };
  renderSidebar();
})();

/* ---- 覆盖后重新渲染当前视图 ---- */
(function(){
  // 原 JS 已在补丁前渲染过主页，用新 renderHome 重绘
  if(!homeEl.hidden){ renderHome(); }
})();
"""


def build_html_v2(data_json: str, css: str, js: str) -> str:
    return (
        V2_TEMPLATE
        .replace("__DATA__", data_json)
        .replace("__CSS__", css)
        .replace("__JS__", js)
    )


def main():
    data, _ = build()
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    data_json = data_json.replace("</", "<\\/")

    full_js = APP_JS + "\n" + V2_JS_PATCH
    html = build_html_v2(data_json, V2_CSS, full_js)
    with open(OUT_V2, "w", encoding="utf-8") as f:
        f.write(html)
    size_mb = len(html.encode("utf-8")) / 1024 / 1024
    print(f"[ok] 已生成 {os.path.basename(OUT_V2)}（{size_mb:.2f} MB，{len(data['articles'])} 篇文章）")
    print(f"     原文件 巴菲特投资智慧.html 未改动")


if __name__ == "__main__":
    main()
