@echo off
chcp 65001 >nul
title Reddit Karma Pilot 全栈启动中枢
echo ===================================================
echo  Reddit Karma Pilot 全栈系统一键启动
echo  防封养号中控台 (FastAPI + Vite/Vue3 + MySQL 8.0)
echo ===================================================

echo [1/3] 启动 FastAPI 后端核心引擎 (端口 8001)...
start "Reddit Karma Pilot - Backend (8001)" cmd /k "cd /d %~dp0 && python start_backend.py"

echo [2/3] 启动 Vite 前端工程 (端口 5173)...
start "Reddit Karma Pilot - Frontend (5173)" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo [3/3] 正在等待服务就绪并打开中控台...
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo ===================================================
echo 🚀 全栈系统就绪！
echo - 前端工作台: http://localhost:5173
echo - 后端 Swagger: http://127.0.0.1:8001/docs
echo ===================================================
