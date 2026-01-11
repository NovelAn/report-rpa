#!/bin/bash
# 测试脚本包装器 - 解决MKL库问题

export MKL_NUM_THREADS=1
export MKL_THREADING_LAYER=GNU
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1

echo "运行MBR自动化系统测试..."
echo "============================"

python test_phase1.py "$@"
