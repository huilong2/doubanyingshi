# 数据库结构文档

本文档详细描述了项目主数据库 `accounts.db` 的内部表结构。

---

## 表: `accounts`

管理用户账号信息。

| 字段名           | 数据类型 | 约束                | 描述                   |
| ---------------- | -------- | ------------------- | ---------------------- |
| id               | INTEGER  | PRIMARY KEY, AUTOINCREMENT | 唯一标识符             |
| username         | TEXT     | UNIQUE, NOT NULL    | 账号用户名             |
| password         | TEXT     |                     | 账号密码               |
| ck               | TEXT     |                     | Cookie 信息            |
| nickname         | TEXT     |                     | 账号昵称               |
| account_id       | TEXT     |                     | 平台上的唯一账号ID     |
| login_status     | TEXT     |                     | 登录状态 (例如, "已登录") |
| homepage         | TEXT     |                     | 用户主页地址           |
| login_time       | TEXT     |                     | 上次登录时间           |
| proxy            | TEXT     |                     | 绑定的代理IP地址       |
| running_status   | TEXT     |                     | 当前运行状态 (例如, "空闲") |
| note             | TEXT     |                     | 备注信息               |
| zhiwenshuju      | TEXT     |                     | 指纹数据 (JSON格式)    |
| gouxuan          | INTEGER  | DEFAULT 0           | 是否在界面上勾选 (1=是, 0=否) |

字段顺序:
0: id
1: username
2: password
3: ck
4: nickname
5: account_id
6: login_status
7: homepage
8: login_time
9: proxy
10: running_status
11: note
12: zhiwenshuju
13: gouxuan
---

## 表: `movies`

存储旧版的电影数据，主要用于特定或随机评星功能。

| 字段名       | 数据类型  | 约束        | 描述                               |
| ------------ | --------- | ----------- | ---------------------------------- |
| id           | INTEGER   | PRIMARY KEY, AUTOINCREMENT | 唯一标识符                         |
| movie_id     | TEXT      | NOT NULL    | 电影的ID                           |
| rating       | TEXT      |             | 用户设置的星级 (例如, "5")         |
| type         | TEXT      | NOT NULL    | 类型 ('specific' 或 'random')      |
| created_at   | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 记录创建时间                       |

---

## 表: `contents`

存储用于发布内容的文本，如评论、说说等。

| 字段名     | 数据类型  | 约束        | 描述                               |
| ---------- | --------- | ----------- | ---------------------------------- |
| id         | INTEGER   | PRIMARY KEY, AUTOINCREMENT | 唯一标识符                         |
| content    | TEXT      | NOT NULL    | 具体的文本内容                     |
| type       | TEXT      | NOT NULL    | 类型 ('specific' 或 'random')      |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 记录创建时间                       |

---

## 表: `dianying` (电影)

存储详细的电影信息。

| 字段名      | 数据类型 | 约束                | 描述           |
| ----------- | -------- | ------------------- | -------------- |
| id          | INTEGER  | PRIMARY KEY, AUTOINCREMENT | 唯一标识符     |
| dianying_id | TEXT     | NOT NULL, UNIQUE    | 电影的平台ID   |
| mingcheng   | TEXT     | NOT NULL            | 电影名称       |
| niandai     | TEXT     |                     | 上映年代       |

---

## 表: `dianshi` (电视)

存储详细的电视剧信息。

| 字段名     | 数据类型 | 约束                | 描述           |
| ---------- | -------- | ------------------- | -------------- |
| id         | INTEGER  | PRIMARY KEY, AUTOINCREMENT | 唯一标识符     |
| dianshi_id | TEXT     | NOT NULL, UNIQUE    | 电视剧的平台ID |
| mingcheng  | TEXT     | NOT NULL            | 电视剧名称     |
| niandai    | TEXT     |                     | 上映年代       |

---

## 表: `yinyue` (音乐)

存储详细的音乐信息。

| 字段名     | 数据类型 | 约束                | 描述         |
| ---------- | -------- | ------------------- | ------------ |
| id         | INTEGER  | PRIMARY KEY, AUTOINCREMENT | 唯一标识符   |
| yinyue_id  | TEXT     | NOT NULL, UNIQUE    | 音乐的平台ID |
| mingcheng  | TEXT     | NOT NULL            | 音乐名称     |
| niandai    | TEXT     |                     | 发行年代     |

---

## 表: `dushu` (读书)

存储详细的书籍信息。

| 字段名    | 数据类型 | 约束                | 描述         |
| --------- | -------- | ------------------- | ------------ |
| id        | INTEGER  | PRIMARY KEY, AUTOINCREMENT | 唯一标识符   |
| dushu_id  | TEXT     | NOT NULL, UNIQUE    | 书籍的平台ID |
| mingcheng | TEXT     | NOT NULL            | 书籍名称     |
| niandai   | TEXT     |                     | 出版年代     |

