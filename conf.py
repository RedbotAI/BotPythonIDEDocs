# BotPython 使用手册 —— Sphinx 配置
# 源目录即本目录（docs/8.user）。原 Markdown 文件同时被软件内“阅读图文用户手册”读取，
# 因此：不得重命名、不得引入 MyST 专有语法，只保持纯 CommonMark。

import os

project = 'BotPython 使用手册'
copyright = '2026, BotPython'
author = 'BotPython'
language = 'zh_CN'

extensions = [
    'myst_parser',
]

source_suffix = {
    '.md': 'markdown',
    '.rst': 'restructuredtext',
}
root_doc = 'index'

# Markdown 标题生成锚点，便于站内定位
myst_heading_anchors = 3

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'navigation_depth': 3,
    'collapse_navigation': False,
    'sticky_navigation': True,
}
html_title = 'BotPython 使用手册'

# 拷贝示例代码与清单：Markdown 中的相对链接 examples/... 需要这些文件在线可下载
html_extra_path = ['examples']

# 内部测试证据（evidence/ 下的原始 JSON/txt）不对外发布
exclude_patterns = ['evidence/**']

# 用户手册.md 中有一条指向 ../7.development/ 的跨目录链接（应用内有效，但超出本站发布范围），
# 该链接在发布的站点上无对应文档，myst 会报 xref_missing 警告。此处按已知情况屏蔽该警告。
suppress_warnings = ['myst.xref_missing']


def _remove_internal_evidence(app, exception):
    """构建结束后删除被测试记录链接、但不应对外发布的原始证据下载。

    myst 会把 Markdown 里链接到的非文档文件（如 evidence/board-results.json）当作
    “可下载文件”拷贝到 _downloads/<hash>/ 下。此处按“evidence 不对外发布”的要求删除，
    使本地构建与 Read the Docs 构建行为一致。删除后测试记录页中对应的“原始证据”链接会失效，
    属预期：原始数据仅保留在仓库内，不随站点公开。
    """
    if exception is not None:
        return
    downloads = os.path.join(app.outdir, '_downloads')
    if not os.path.isdir(downloads):
        return
    for sub in os.listdir(downloads):
        d = os.path.join(downloads, sub)
        if not os.path.isdir(d):
            continue
        for name in ('board-results.json', 'regression.txt'):
            p = os.path.join(d, name)
            if os.path.exists(p):
                os.remove(p)
        if not os.listdir(d):
            os.rmdir(d)


def setup(app):
    app.connect('build-finished', _remove_internal_evidence)
