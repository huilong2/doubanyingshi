# UI 组件与代码变量映射文档

本文档旨在映射程序界面上的各个组件到 `main.py` 文件中对应的代码变量名，以便于快速查找和修改。

---

## 主窗口 (`AccountManagerWindow`)

| 组件描述 | 变量名 |
| --- | --- |
| 主标签页容器 | `self.tab_widget` |

---

## 1. 账号管理标签页 (`init_account_tab`)

| 组件描述 | 变量名 |
| --- | --- |
| 账号信息表格 | `self.account_table` |
| "全选" 按钮 | `self.select_all_btn` |
| "取消" 按钮 | `self.deselect_all_btn` |
| "添加账号" 按钮 | `self.add_account_btn` |
| "编辑账号" 按钮 | `self.edit_account_btn` |
| "删除账号" 按钮 | `self.delete_account_btn` |
| "打开浏览器" 按钮 | `self.open_browser_btn` |
| "添加代理" 按钮 | `self.add_proxy_btn` |
| "删除代理" 按钮 | `self.remove_proxy_btn` |

---

## 2. 电影管理标签页 (`init_movie_tab`)

| 组件描述 | 变量名 |
| --- | --- |
| 指定电影表格 | `self.movie_specific_table` |
| 随机电影表格 | `self.movie_random_table` |

*注：此标签页中的 "添加"、"删除"、"更新星级" 等按钮是在 `init_movie_tab` 方法内部创建的局部变量，没有被赋给 `self`。它们的点击事件直接连接到了对应的处理函数。*

---

## 3. 内容管理标签页 (`init_content_tab`)

| 组件描述 | 变量名 |
| --- | --- |
| 指定内容表格 | `self.content_specific_table` |
| 随机内容表格 | `self.content_random_table` |

*注：此标签页中的 "添加"、"删除" 等按钮是局部变量，与电影管理标签页类似。*

---

## 4. 功能设置标签页 (`init_function_tab`)

| 组件描述 | 变量名 |
| --- | --- |
| **功能选择** | |
| "签名" 复选框 | `self.signature_checkbox` |
| "说说" 复选框 | `self.status_checkbox` |
| "小组" 复选框 | `self.group_checkbox` |
| "短语" 复选框 | `self.phrase_checkbox` |
| **间隔设置** | |
| 操作间隔 (最小) | `self.operation_interval_min` |
| 操作间隔 (最大) | `self.operation_interval_max` |
| 换号间隔 (最小) | `self.account_interval_min` |
| 换号间隔 (最大) | `self.account_interval_max` |
| 错误间隔 (最小) | `self.error_interval_min` |
| 错误间隔 (最大) | `self.error_interval_max` |
| **评星设置** | |
| 随机评星 (最小) | `self.rating_min` |
| 随机评星 (最大) | `self.rating_max` |
| 随机百分比评论 | `self.random_comment_percentage` |
| 评星星级输入框 | `self.star_rating` |
| 评星类型下拉框 | `self.rating_type` |
| **输入内容** | |
| 内容输入文本框 | `self.content_text` |
| **运行设置** | |
| "开始" 按钮 | `self.run_start_btn` |
| 运行模式下拉框 | `self.run_mode_combo` |
| 运行状态下拉框 | `self.run_status_combo` |
| Cookie 更新时间输入框 | `self.run_cookie_time` |
| "开启代理" 复选框 | `self.enable_proxy_checkbox` |

---

## 5. 数据库管理标签页 (`init_database_tab`)

| 组件描述 | 变量名 |
| --- | --- |
| 左侧数据库表列表 | `self.database_table` |
| 右侧数据详情表格 | `self.data_detail_table` |
| "刷新数据" 按钮 | `self.db_refresh_button` |

---

## 6. 程序设置标签页 (`init_settings_tab`)

| 组件描述 | 变量名 |
| --- | --- |
| 浏览器路径输入框 | `self.browser_path_edit` |
| 缓存路径输入框 | `self.cache_path_edit` |

*注：此标签页中的 "自动检测" 和 "浏览" 按钮是局部变量。*

