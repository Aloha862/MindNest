# 智学空间(MindNest) 前端

Vue 3 + Vite 实现的课程设计前端，默认使用 mock 数据演示完整流程。

## 启动

```bash
npm install
npm run dev
```

## 构建

```bash
npm run build
```

## 演示账号

- 普通用户：`demo`，任意非空密码
- 管理员：`admin`，任意非空密码

## 结构

- `src/api`：统一接口封装，后续替换 FastAPI 时保持方法签名即可
- `src/mock`：演示数据与模拟请求
- `src/router`：路由和权限守卫
- `src/stores`：Pinia 状态
- `src/layouts`：认证、用户端、管理员端布局
- `src/views`：页面
- `src/components`：通用业务组件
- `src/styles`：主题变量与全局样式
