


import shutil
from pathlib import Path
import os

# 脚本工具箱
# 集成一些额外的办公用的脚本

def batch_convert_py_to_txt(source_paths_list, target_path=None):
    """
    逻辑函数：遍历 source_paths_list 中的所有文件夹，将 .py 转为 .txt
    source_paths_list: list, 包含多个文件夹路径的列表
    target_path: str, 汇总的目标文件夹 (可选)
    返回: (bool, str) -> (是否成功, 提示信息)
    """
    logs = []
    total_count = 0

    # str转Path对象，以便后续的拼接操作
    target_root = Path(target_path) if target_path else None

    # 1. 遍历所有源文件夹
    for src_path_str in source_paths_list:
        src_path = Path(src_path_str)  # 解析成path对象，以便调用方法
        
        if not src_path.exists():
            logs.append(f"⚠️ 跳过不存在的路径: {src_path_str}")
            continue

        logs.append(f"📂 正在扫描: {src_path.name} ...")
        
        try:
            # 开始扫描文件
            folder_count = 0
            for py_file in src_path.glob('*.py'):  # 遍历并查找.py结尾的文件
                try:
                    new_filename = py_file.name.replace('.py', '.txt')  # 构建替换后缀后的文件名
                    dest_file = target_root / new_filename              # 构建目的文件路径，就是传入的目录
                    shutil.copy2(py_file, dest_file)                    # 复制文件内容至指定文件路径
                    folder_count += 1
                except Exception as e:
                    logs.append(f"  ❌ 转换失败: {py_file.name} - {str(e)}")
            
            total_count += folder_count
            logs.append(f"  ✅ 已处理 {folder_count} 个文件 -> {target_root}")
            
        except Exception as e:
            logs.append(f"❌ 文件夹处理失败 {src_path}: {str(e)}")

    summary = f"\n🎉 全部完成！共转换 {total_count} 个文件。"
    return True, "\n".join(logs + [summary])
