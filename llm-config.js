/* 可选 LLM 默认配置（由 build_buffett_app.py 生成，不含任何密钥）。
 * 密钥不落盘：用「启动巴菲特知识库.command」启动时，本地服务器会从
 * 环境变量 DEEPSEEK_API_KEY（或项目根 .env）动态注入；也可在应用
 * 「设置」面板手动填写（仅保存在本浏览器 localStorage）。
 * 修改本文件后刷新页面即可生效。 */
window.BUFFETT_LLM_CONFIG = {
  base: "https://api.deepseek.com/v1",
  key: "",
  model: "deepseek-v4-flash"
};
