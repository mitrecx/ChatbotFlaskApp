为了使项目正常运行, 需要在项目根目录下新建 `.env` 文件, 并添加以下内容:
```bash
ARK_API_KEY=e9ee34d9-xxxx-416e-a722-xxxxxxxxxxxx
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```
其中 `ARK_API_KEY` 是你的 Ark 密钥, 请替换为实际的值。
`ARK_API_KEY` 的获取方式:
1. 登录 [Ark 控制台](https://console.volcengine.com/ark/region:ark+cn-beijing/endpoint?config=%7B%7D)
2. 创建在线接入点
3. 选择 API 调用 -> 通过 API Key 授权
4. 复制显示的 API 密钥

注意: 要把`.env` 文件路径配置在启动参数中.

