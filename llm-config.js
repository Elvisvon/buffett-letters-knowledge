/* 可选 LLM 默认配置（由 build_buffett_app.py 生成，不含任何密钥）。
 * 服务端密钥不写入应用状态或生成物，仅通过同源 /api/llm-config 注入页面内存；
 * 也可在应用「设置」面板手动填写（仅保存在本浏览器 localStorage）。
 * 修改本文件后刷新页面即可生效。 */
window.BUFFETT_LLM_CONFIG = {
  base: "https://api.deepseek.com/v1",
  key: "",
  model: "deepseek-v4-flash"
};
