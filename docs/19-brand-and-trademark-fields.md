# Brand And Trademark Fields

本文档定义从源码开始使用的正式品牌字段。

## 1. 决策

产品的默认品牌、logo 文案和商标字段统一为：

```text
bairui
```

Hermes 是后端内核工程名，MOXI-cloud-agent 是平台仓库工程名。它们不等同于最终客户看到的品牌字段。

## 2. Runtime Fields

Hermes runtime 默认读取：

- `BAIRUI_PRODUCT_NAME`
- `BAIRUI_BRAND_KEY`
- `BAIRUI_TRADEMARK_NAME`
- `BAIRUI_LOGO_TEXT`

默认值：

```text
BAIRUI_PRODUCT_NAME=bairui Agent OS
BAIRUI_BRAND_KEY=bairui
BAIRUI_TRADEMARK_NAME=bairui
BAIRUI_LOGO_TEXT=bairui
```

## 3. API Output

`/health` 必须返回品牌字段：

```json
{
  "brand": {
    "key": "bairui",
    "trademark": "bairui",
    "logo_text": "bairui"
  }
}
```

## 4. Commercial Rule

所有客户可见 UI、license、部署向导、官网、控制台和服务器 Agent 默认品牌字段应使用 `bairui`。

工程名可以保留：

- Hermes：Agent OS 后端内核；
- MOXI-cloud-agent：商业平台和服务器管理仓库。
