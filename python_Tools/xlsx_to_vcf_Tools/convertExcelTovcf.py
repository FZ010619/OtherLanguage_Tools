import pandas as pd
import os

'''
主要用来批量转化手机号从xlsx到vcf,方便手机通讯录使用
mainly use to convert Phone From xlsx to vcf  ,it will help you import a huge number of Phone number.
'''


def xlsx_to_vcf(excel_file, vcf_file):
    # 自动使用脚本同目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(script_dir, excel_file)
    df = pd.read_excel(excel_path)

    print("检测到的列名：", df.columns.tolist())
    print("前5行数据预览：\n", df.head())

    # 自动匹配常见姓名和电话列名
    name_candidates = ['姓名', '名字', '联系人', 'Name', '姓名名称']
    phone_candidates = ['电话', '手机', '手机号', '联系电话', '手机号码', 'Phone', 'TEL']

    name_col = next((col for col in df.columns if col.strip()
                    in name_candidates), df.columns[0])  # 默认第一列
    phone_col = next((col for col in df.columns if col.strip(
    ) in phone_candidates), df.columns[1] if len(df.columns) > 1 else None)

    print(f"使用姓名列: {name_col}")
    print(f"使用电话列: {phone_col}")

    vcf_path = os.path.join(script_dir, vcf_file)
    with open(vcf_path, 'w', encoding='utf-8') as f:
        for _, row in df.iterrows():
            f.write("BEGIN:VCARD\n")
            f.write("VERSION:3.0\n")

            # 姓名
            name = str(row[name_col]).strip()
            if name and name != 'nan':
                f.write(f"FN:{name}\n")
                f.write(f"N:{name};;;;\n")  # 结构化姓名（可选）

            # 电话（清理空格、横杠）
            if phone_col and phone_col in row:
                phone = str(row[phone_col]).strip().replace(
                    ' ', '').replace('-', '')
                if phone and phone != 'nan':
                    f.write(f"TEL;TYPE=CELL:{phone}\n")

            f.write("END:VCARD\n")

    print(f"成功生成 {len(df)} 个联系人 → {vcf_path}")
    print("已自动去除多余的外层 VCARD，导入手机应该正常！")


# 调用（改成你的实际文件名）
xlsx_to_vcf('test.xlsx', 'test.vcf')
