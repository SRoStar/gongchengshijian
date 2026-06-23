# -*- coding: utf-8 -*-
import sqlite3
import json
from pathlib import Path

# =============== 模拟数据字典 (已转换为 Python 格式) ===============
mock_users = [
    {"id": 1, "username": "admin", "email": "admin@ustc.edu.cn", "password": "admin123", "role": "admin", "nickname": "管理员", "phone": "13800138000", "avatar": "", "createTime": "2024-01-01"},
    {"id": 2, "username": "user1", "email": "user1@ustc.edu.cn", "password": "user123", "role": "user", "nickname": "用户1", "phone": "13800138001", "avatar": "", "createTime": "2024-02-01"},
    {"id": 3, "username": "researcher", "email": "researcher@ustc.edu.cn", "password": "test123", "role": "user", "nickname": "研究人员", "phone": "13800138002", "avatar": "", "createTime": "2024-03-01"}
]

mock_news = [
    {"id": 1, "title": "精准化学数据平台正式上线运行", "content": "<p>经过数年的建设与测试，精准化学数据平台（PIChemData）于近日正式上线运行。该平台集成了大量的化学分子数据、材料数据和文献数据，为广大科研工作者提供便捷的数据检索和分析服务。</p><p>平台目前收录了超过10万条分子数据、5万条材料数据以及相关文献信息。用户可以通过平台进行分子结构搜索、相似性分析、材料性质查询等多种操作。</p>", "author": "管理员", "createTime": "2025-12-01 10:00:00", "summary": "精准化学数据平台正式上线运行，集成大量化学数据资源。"},
    {"id": 2, "title": "平台新增AI智能助手功能", "content": "<p>为进一步提升用户体验，精准化学数据平台近日推出了AI智能助手功能。用户可以通过自然语言输入，快速查询化学元素信息、分子结构、材料性质等数据。</p><p>智能助手支持中英文双语交互，能够理解复杂的化学查询需求，并给出准确的数据反馈。该功能基于大语言模型技术开发，将持续优化和改进。</p>", "author": "产品团队", "createTime": "2025-12-15 14:30:00", "summary": "新增AI智能助手，支持自然语言查询化学数据。"},
    {"id": 3, "title": "数据更新：新增过渡金属催化剂数据集", "content": "<p>平台最新收录了一批过渡金属催化剂数据集，涵盖Fe、Co、Ni、Cu、Pd、Pt等多种过渡金属的催化体系。数据来源于国内外高水平期刊论文和实验测量结果。</p><p>该数据集包含催化剂结构信息、反应条件、催化性能指标等详细信息，可用于机器学习模型训练和催化机理研究。</p>", "author": "数据团队", "createTime": "2025-12-28 09:00:00", "summary": "新增过渡金属催化剂数据集。"},
    {"id": 4, "title": "API接口更新公告", "content": "<p>精准化学数据平台API接口已升级至v1.2版本，新增分子相似性搜索接口、材料性质批量查询接口等功能。请各位开发者及时更新您的应用程序。</p><p>详细接口文档请参见API信息页面。</p>", "author": "技术团队", "createTime": "2026-01-10 16:00:00", "summary": "API接口升级至v1.2，新增多项功能。"},
    {"id": 5, "title": "平台获得国家自然科学基金资助", "content": "<p>精准化学数据平台建设项目获得国家自然科学基金面上项目资助。项目将重点建设高质量化学数据的标准化收集、管理和共享机制。</p>", "author": "项目组", "createTime": "2026-02-20 11:00:00", "summary": "获得国家自然科学基金资助。"}
]

mock_announcements = [
    {"id": 1, "title": "系统维护通知：2026年1月15日凌晨2:00-6:00", "content": "<p>尊敬的平台用户：</p><p>为提升系统性能和稳定性，平台将于2026年1月15日凌晨2:00至6:00进行系统维护升级。维护期间平台将暂停服务，给您带来的不便敬请谅解。</p><p>如有紧急需求，请联系管理员邮箱：admin@ustc.edu.cn</p>", "author": "系统管理员", "createTime": "2026-01-10", "importance": "high"},
    {"id": 2, "title": "关于数据入库标准的补充说明", "content": "<p>为提高平台数据质量，现将数据入库标准补充说明如下：</p><p>1. 所有上传数据须包含完整的元数据信息<br>2. 分子数据须提供SMILES或InChI标识符<br>3. 计算数据须注明计算方法和基组信息</p>", "author": "数据管理组", "createTime": "2026-01-20", "importance": "medium"},
    {"id": 3, "title": "2026年春节假期服务安排", "content": "<p>根据学校统一安排，平台运营团队春节期间（2026年2月17日-2月25日）将采用在线值班方式。期间平台正常运行，但数据处理和审核可能会有延迟。</p>", "author": "运营团队", "createTime": "2026-02-10", "importance": "low"},
    {"id": 4, "title": "化学数据标准研讨会通知", "content": "<p>兹定于2026年3月15日举办\"化学数据标准化与共享\"在线研讨会，欢迎各位同仁参加。</p><p>会议日程及报名方式请参见附件。</p>", "author": "学术委员会", "createTime": "2026-03-01", "importance": "medium"}
]

mock_molecules = [
    {"id": 1, "formula": "H2O", "smiles": "O", "inchi": "InChI=1S/H2O/h1H2", "mass": 18.015, "volume": 18.07, "type": "无机小分子", "tags": ["水", "溶剂", "无机"], "charge": 0, "spin": 1, "atoms": ["H", "H", "O"], "bonds": [[0, 2, 1], [1, 2, 1]], "createTime": "2025-12-01"},
    {"id": 2, "formula": "CH4", "smiles": "C", "inchi": "InChI=1S/CH4/h1H4", "mass": 16.043, "volume": 24.45, "type": "有机小分子", "tags": ["甲烷", "烷烃", "天然气"], "charge": 0, "spin": 1, "atoms": ["C", "H", "H", "H", "H"], "bonds": [[0, 1, 1], [0, 2, 1], [0, 3, 1], [0, 4, 1]], "createTime": "2025-12-01"},
    {"id": 3, "formula": "C2H5OH", "smiles": "CCO", "inchi": "InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3", "mass": 46.069, "volume": 58.37, "type": "有机小分子", "tags": ["乙醇", "醇类", "溶剂"], "charge": 0, "spin": 1, "atoms": ["C", "C", "O", "H", "H", "H", "H", "H", "H"], "bonds": [[0, 1, 1], [1, 2, 1], [0, 3, 1], [0, 4, 1], [0, 5, 1], [1, 6, 1], [1, 7, 1], [2, 8, 1]], "createTime": "2025-12-02"},
    {"id": 4, "formula": "C6H6", "smiles": "c1ccccc1", "inchi": "InChI=1S/C6H6/c1-2-4-6-5-3-1/h1-6H", "mass": 78.114, "volume": 89.24, "type": "芳香族化合物", "tags": ["苯", "芳香族", "有机溶剂"], "charge": 0, "spin": 1, "atoms": ["C", "C", "C", "C", "C", "C", "H", "H", "H", "H", "H", "H"], "bonds": [[0, 1, 2], [1, 2, 1], [2, 3, 2], [3, 4, 1], [4, 5, 2], [5, 0, 1], [0, 6, 1], [1, 7, 1], [2, 8, 1], [3, 9, 1], [4, 10, 1], [5, 11, 1]], "createTime": "2025-12-02"},
    {"id": 5, "formula": "CO2", "smiles": "O=C=O", "inchi": "InChI=1S/CO2/c2-1-3", "mass": 44.009, "volume": 29.69, "type": "无机小分子", "tags": ["二氧化碳", "温室气体", "无机"], "charge": 0, "spin": 1, "atoms": ["C", "O", "O"], "bonds": [[0, 1, 2], [0, 2, 2]], "createTime": "2025-12-03"},
    {"id": 6, "formula": "NH3", "smiles": "N", "inchi": "InChI=1S/H3N/h1H3", "mass": 17.031, "volume": 22.41, "type": "无机小分子", "tags": ["氨", "无机", "碱"], "charge": 0, "spin": 1, "atoms": ["N", "H", "H", "H"], "bonds": [[0, 1, 1], [0, 2, 1], [0, 3, 1]], "createTime": "2025-12-03"},
    {"id": 7, "formula": "CH3COOH", "smiles": "CC(=O)O", "inchi": "InChI=1S/C2H4O2/c1-2(3)4/h1H3,(H,3,4)", "mass": 60.052, "volume": 57.06, "type": "有机小分子", "tags": ["乙酸", "羧酸", "有机酸"], "charge": 0, "spin": 1, "atoms": ["C", "C", "O", "O", "H", "H", "H", "H"], "bonds": [[0, 1, 1], [1, 2, 2], [1, 3, 1], [0, 4, 1], [0, 5, 1], [0, 6, 1], [3, 7, 1]], "createTime": "2025-12-04"},
    {"id": 8, "formula": "C3H8O", "smiles": "CCCO", "inchi": "InChI=1S/C3H8O/c1-2-3-4/h4H,2-3H2,1H3", "mass": 60.096, "volume": 75.17, "type": "有机小分子", "tags": ["正丙醇", "醇类", "溶剂"], "charge": 0, "spin": 1, "createTime": "2025-12-04"},
    {"id": 9, "formula": "NaCl", "smiles": "[Na+].[Cl-]", "inchi": "InChI=1S/ClH.Na/h1H;/q;+1/p-1", "mass": 58.44, "volume": 27.02, "type": "无机盐", "tags": ["氯化钠", "盐", "无机"], "charge": 0, "spin": 1, "createTime": "2025-12-05"},
    {"id": 10, "formula": "C2H4", "smiles": "C=C", "inchi": "InChI=1S/C2H4/c1-2/h1-2H2", "mass": 28.054, "volume": 22.41, "type": "烯烃", "tags": ["乙烯", "烯烃", "石化原料"], "charge": 0, "spin": 1, "createTime": "2025-12-05"},
    {"id": 11, "formula": "H2SO4", "smiles": "OS(=O)(=O)O", "inchi": "InChI=1S/H2O4S/c1-5(2,3)4/h(H2,1,2,3,4)", "mass": 98.079, "volume": 53.62, "type": "无机酸", "tags": ["硫酸", "强酸", "无机酸"], "charge": 0, "spin": 1, "createTime": "2025-12-06"},
    {"id": 12, "formula": "C7H8", "smiles": "Cc1ccccc1", "inchi": "InChI=1S/C7H8/c1-7-5-3-2-4-6-7/h2-6H,1H3", "mass": 92.141, "volume": 106.29, "type": "芳香族化合物", "tags": ["甲苯", "芳香族", "溶剂"], "charge": 0, "spin": 1, "createTime": "2025-12-06"}
]

mock_materials = [
    {"id": 1, "name": "Cu(111)表面", "formula": "Cu", "type": "金属表面", "tags": ["铜", "表面", "催化", "过渡金属"], "bandGap": None, "latticeConstant": 3.615, "crystalSystem": "面心立方", "spaceGroup": "Fm-3m", "createTime": "2025-12-01"},
    {"id": 2, "name": "TiO2锐钛矿", "formula": "TiO2", "type": "金属氧化物", "tags": ["二氧化钛", "光催化", "半导体"], "bandGap": 3.2, "latticeConstant": 3.785, "crystalSystem": "四方", "spaceGroup": "I41/amd", "createTime": "2025-12-02"},
    {"id": 3, "name": "石墨烯", "formula": "C", "type": "二维材料", "tags": ["石墨烯", "二维材料", "碳材料"], "bandGap": 0, "latticeConstant": 2.46, "crystalSystem": "六方", "spaceGroup": "P6/mmm", "createTime": "2025-12-03"},
    {"id": 4, "name": "ZnO纤锌矿", "formula": "ZnO", "type": "金属氧化物", "tags": ["氧化锌", "半导体", "压电材料"], "bandGap": 3.37, "latticeConstant": 3.249, "crystalSystem": "六方", "spaceGroup": "P63mc", "createTime": "2025-12-04"},
    {"id": 5, "name": "Fe2O3赤铁矿", "formula": "Fe2O3", "type": "金属氧化物", "tags": ["氧化铁", "磁性材料", "催化剂"], "bandGap": 2.2, "latticeConstant": 5.036, "crystalSystem": "六方", "spaceGroup": "R-3c", "createTime": "2025-12-05"},
    {"id": 6, "name": "Pt(111)表面", "formula": "Pt", "type": "金属表面", "tags": ["铂", "表面", "催化", "贵金属"], "bandGap": None, "latticeConstant": 3.924, "crystalSystem": "面心立方", "spaceGroup": "Fm-3m", "createTime": "2025-12-06"},
    {"id": 7, "name": "MoS2单层", "formula": "MoS2", "type": "二维材料", "tags": ["二硫化钼", "二维材料", "TMD"], "bandGap": 1.8, "latticeConstant": 3.16, "crystalSystem": "六方", "spaceGroup": "P63/mmc", "createTime": "2025-12-07"},
    {"id": 8, "name": "Al2O3刚玉", "formula": "Al2O3", "type": "金属氧化物", "tags": ["氧化铝", "陶瓷", "载体"], "bandGap": 8.7, "latticeConstant": 4.759, "crystalSystem": "三方", "spaceGroup": "R-3c", "createTime": "2025-12-08"}
]

mock_literature = [
    {"id": 1, "doi": "10.1021/jacs.5b01234", "title": "Density Functional Theory Study of CO2 Reduction on Transition Metal Surfaces", "authors": "Zhang, L.; Wang, H.; Li, J.", "journal": "Journal of the American Chemical Society", "year": 2025, "volume": "137", "issue": "15", "pages": "5123-5130", "abstract": "A comprehensive DFT study of CO2 reduction reaction mechanisms on various transition metal surfaces, including Cu, Ag, Au, and Pt.", "keywords": ["CO2 reduction", "DFT", "transition metals", "catalysis"], "tags": ["催化", "DFT计算", "过渡金属"]},
    {"id": 2, "doi": "10.1038/s41563-024-01789-0", "title": "Machine Learning Accelerated Discovery of Novel Perovskite Materials for Solar Cells", "authors": "Chen, X.; Liu, Y.; Wang, Z.; et al.", "journal": "Nature Materials", "year": 2025, "volume": "24", "issue": "3", "pages": "301-310", "abstract": "Using machine learning models trained on high-throughput DFT calculations to screen novel perovskite compositions for photovoltaic applications.", "keywords": ["machine learning", "perovskite", "solar cells", "high-throughput screening"], "tags": ["机器学习", "钙钛矿", "太阳能电池"]},
    {"id": 3, "doi": "10.1002/anie.2024112345", "title": "Single-Atom Catalysts for Efficient Nitrogen Reduction Reaction", "authors": "Wang, F.; Zhang, Q.; Li, M.", "journal": "Angewandte Chemie International Edition", "year": 2025, "volume": "64", "issue": "8", "pages": "e2024112345", "abstract": "Design and synthesis of single-atom catalysts supported on N-doped carbon for electrochemical nitrogen reduction to ammonia.", "keywords": ["single-atom catalyst", "nitrogen reduction", "electrocatalysis"], "tags": ["单原子催化", "氮还原", "电催化"]},
    {"id": 4, "doi": "10.1126/science.ade1234", "title": "Direct Observation of Chemical Reaction Dynamics at Single-Molecule Level", "authors": "Johnson, R.; Smith, A.; Brown, T.", "journal": "Science", "year": 2026, "volume": "381", "issue": "6654", "pages": "456-460", "abstract": "Using advanced microscopy techniques to observe individual chemical reaction events in real-time at the single-molecule level.", "keywords": ["single-molecule", "reaction dynamics", "microscopy"], "tags": ["单分子", "反应动力学", "显微技术"]},
    {"id": 5, "doi": "10.1039/D4SC05678-9", "title": "Data-Driven Design of Metal-Organic Frameworks for Gas Separation", "authors": "Li, H.; Kim, J.; Park, S.", "journal": "Chemical Science", "year": 2025, "volume": "16", "issue": "12", "pages": "2890-2905", "abstract": "A data-driven approach combining molecular simulation and machine learning for screening MOFs for CO2/N2 and CO2/CH4 separation.", "keywords": ["MOF", "gas separation", "machine learning", "molecular simulation"], "tags": ["MOF", "气体分离", "机器学习"]}
]

mock_molecule_tags = [
    {"id": 1, "name": "溶剂", "count": 45, "category": "应用"},
    {"id": 2, "name": "催化剂", "count": 38, "category": "应用"},
    {"id": 3, "name": "有机", "count": 120, "category": "类型"},
    {"id": 4, "name": "无机", "count": 89, "category": "类型"},
    {"id": 5, "name": "芳香族", "count": 56, "category": "结构"},
    {"id": 6, "name": "烷烃", "count": 34, "category": "结构"},
    {"id": 7, "name": "烯烃", "count": 28, "category": "结构"},
    {"id": 8, "name": "醇类", "count": 42, "category": "官能团"},
    {"id": 9, "name": "羧酸", "count": 25, "category": "官能团"},
    {"id": 10, "name": "过渡金属", "count": 67, "category": "元素"},
    {"id": 11, "name": "半导体", "count": 30, "category": "性质"},
    {"id": 12, "name": "二维材料", "count": 22, "category": "结构"}
]

mock_material_tags = [
    {"id": 1, "name": "催化", "count": 55, "category": "应用"},
    {"id": 2, "name": "光催化", "count": 28, "category": "应用"},
    {"id": 3, "name": "半导体", "count": 35, "category": "性质"},
    {"id": 4, "name": "金属", "count": 80, "category": "类型"},
    {"id": 5, "name": "氧化物", "count": 60, "category": "类型"},
    {"id": 6, "name": "二维材料", "count": 25, "category": "结构"},
    {"id": 7, "name": "表面", "count": 40, "category": "结构"},
    {"id": 8, "name": "磁性材料", "count": 18, "category": "性质"},
    {"id": 9, "name": "钙钛矿", "count": 15, "category": "结构"},
    {"id": 10, "name": "陶瓷", "count": 20, "category": "类型"}
]


mock_audit_logs = [
    {"id": 1, "userId": 1, "username": "admin", "action": "登录", "resource": "系统", "detail": "用户登录成功", "ip": "202.38.64.1", "time": "2026-01-15 08:30:00"},
    {"id": 2, "userId": 2, "username": "user1", "action": "查询", "resource": "分子数据", "detail": "搜索关键词：H2O", "ip": "202.38.64.2", "time": "2026-01-15 09:15:00"},
    {"id": 3, "userId": 1, "username": "admin", "action": "创建", "resource": "元数据", "detail": "创建元数据字段：计算方法", "ip": "202.38.64.1", "time": "2026-01-15 10:00:00"},
    {"id": 4, "userId": 3, "username": "researcher", "action": "上传", "resource": "数据", "detail": "上传分子数据文件：dataset_2024.json", "ip": "202.38.64.3", "time": "2026-01-15 11:20:00"},
    {"id": 5, "userId": 2, "username": "user1", "action": "下载", "resource": "API", "detail": "通过API下载分子列表", "ip": "202.38.64.2", "time": "2026-01-15 14:45:00"},
    {"id": 6, "userId": 1, "username": "admin", "action": "删除", "resource": "标签", "detail": "删除标签：废弃标签", "ip": "202.38.64.1", "time": "2026-01-15 16:00:00"},
    {"id": 7, "userId": 3, "username": "researcher", "action": "修改", "resource": "账户", "detail": "修改个人信息", "ip": "202.38.64.3", "time": "2026-01-15 17:30:00"}
]

mock_metadata = [
    {"id": 1, "fieldEn": "calculation_method", "fieldZh": "计算方法", "type": "string", "required": True, "description": "使用的计算方法和基组"},
    {"id": 2, "fieldEn": "potential_energy", "fieldZh": "势能", "type": "float", "required": False, "description": "体系总势能 (eV)"},
    {"id": 3, "fieldEn": "temperature", "fieldZh": "温度", "type": "float", "required": False, "description": "计算/实验温度 (K)"},
    {"id": 4, "fieldEn": "pressure", "fieldZh": "压力", "type": "float", "required": False, "description": "计算/实验压力 (Pa)"},
    {"id": 5, "fieldEn": "basis_set", "fieldZh": "基组", "type": "string", "required": False, "description": "计算使用的基组"},
    {"id": 6, "fieldEn": "functional", "fieldZh": "泛函", "type": "string", "required": False, "description": "DFT计算使用的泛函"}
]

mock_spectrum = [
    {
        "picId": 1,
        "spectra": [
            {
                "id": "spec-1-ir", "type": "IR", "name": "H₂O FTIR Spectrum", "instrument": "Bruker VERTEX 70", "conditions": "KBr pellet, 400-4000 cm⁻¹, RT", "xLabel": "Wavenumber (cm⁻¹)", "yLabel": "Transmittance (%)",
                "peaks": [{"x": 3450, "y": 82, "label": "O-H stretch (sym)"}, {"x": 1640, "y": 68, "label": "H-O-H bend"}, {"x": 3756, "y": 88, "label": "O-H stretch (asym)"}, {"x": 660, "y": 42, "label": "O-H libration"}],
                "dataPoints": [[400, 95], [600, 88], [800, 78], [1000, 65], [1200, 72], [1400, 80], [1600, 68], [1800, 85], [2000, 90], [2200, 92], [2400, 93], [2600, 94], [2800, 95], [3000, 90], [3200, 85], [3400, 70], [3600, 60], [3756, 88], [3900, 45], [4000, 40]]
            },
            {
                "id": "spec-1-nmr", "type": "NMR", "name": "¹H NMR Spectrum of H₂O", "instrument": "Bruker AVANCE III 400", "conditions": "D₂O, 400 MHz, 298K", "xLabel": "Chemical Shift (ppm)", "yLabel": "Intensity",
                "peaks": [{"x": 4.79, "y": 90, "label": "HDO (solvent)"}],
                "dataPoints": [[0, 5], [0.5, 6], [1, 8], [1.5, 9], [2, 11], [2.5, 10], [3, 13], [3.5, 15], [4, 22], [4.3, 40], [4.5, 60], [4.7, 85], [4.79, 90], [4.9, 55], [5, 35], [5.5, 18], [6, 12], [7, 8], [8, 5], [9, 3], [10, 2]]
            }
        ]
    },
    {
        "picId": 3,
        "spectra": [
            {
                "id": "spec-3-ir", "type": "IR", "name": "Ethanol FTIR Spectrum", "instrument": "Thermo Nicolet iS50", "conditions": "KBr pellet, 400-4000 cm⁻¹, RT", "xLabel": "Wavenumber (cm⁻¹)", "yLabel": "Transmittance (%)",
                "peaks": [{"x": 3340, "y": 75, "label": "O-H stretch"}, {"x": 2974, "y": 82, "label": "C-H stretch (asym)"}, {"x": 2880, "y": 85, "label": "C-H stretch (sym)"}, {"x": 1050, "y": 60, "label": "C-O stretch"}],
                "dataPoints": [[400, 92], [600, 85], [800, 72], [1000, 62], [1050, 60], [1200, 70], [1400, 78], [1600, 88], [1800, 90], [2000, 92], [2200, 94], [2400, 93], [2600, 88], [2800, 85], [2880, 85], [2974, 82], [3100, 78], [3340, 75], [3500, 60], [3700, 45], [4000, 38]]
            },
            {
                "id": "spec-3-ms", "type": "MS", "name": "Ethanol EI Mass Spectrum", "instrument": "Agilent 5977B GC/MSD", "conditions": "EI 70eV, m/z 10-100", "xLabel": "m/z", "yLabel": "Relative Abundance (%)",
                "peaks": [{"x": 31, "y": 100, "label": "[CH₂OH]⁺"}, {"x": 45, "y": 52, "label": "[C₂H₅O]⁺"}, {"x": 46, "y": 18, "label": "[M]⁺·"}, {"x": 27, "y": 35, "label": "[C₂H₃]⁺"}, {"x": 29, "y": 28, "label": "[C₂H₅]⁺"}],
                "dataPoints": [[10, 2], [15, 10], [18, 8], [20, 5], [25, 15], [27, 35], [29, 28], [31, 100], [35, 8], [40, 12], [43, 20], [45, 52], [46, 18], [47, 3], [50, 5], [55, 3], [60, 1], [70, 1], [80, 0], [100, 0]]
            }
        ]
    },
    {
        "picId": 4,
        "spectra": [
            {
                "id": "spec-4-ir", "type": "IR", "name": "Benzene FTIR Spectrum", "instrument": "Bruker VERTEX 70", "conditions": "KBr pellet, 400-4000 cm⁻¹, RT", "xLabel": "Wavenumber (cm⁻¹)", "yLabel": "Transmittance (%)",
                "peaks": [{"x": 3036, "y": 78, "label": "C-H stretch (arom)"}, {"x": 1480, "y": 55, "label": "C=C ring stretch"}, {"x": 1035, "y": 60, "label": "C-H in-plane bend"}, {"x": 674, "y": 40, "label": "C-H out-of-plane bend"}],
                "dataPoints": [[400, 92], [500, 82], [674, 40], [800, 65], [900, 72], [1000, 62], [1035, 60], [1100, 68], [1200, 75], [1300, 70], [1400, 60], [1480, 55], [1600, 70], [1800, 82], [2000, 85], [2200, 88], [2400, 90], [2600, 85], [2800, 80], [3000, 78], [3036, 78], [3200, 72], [3400, 65], [3600, 50], [4000, 42]]
            },
            {
                "id": "spec-4-uv", "type": "UV-Vis", "name": "Benzene UV-Vis Spectrum", "instrument": "Shimadzu UV-2600", "conditions": "Cyclohexane, 200-400 nm, RT", "xLabel": "Wavelength (nm)", "yLabel": "Absorbance",
                "peaks": [{"x": 255, "y": 0.82, "label": "π→π* (¹B₂ᵤ)"}, {"x": 204, "y": 0.95, "label": "π→π* (¹B₁ᵤ)"}],
                "dataPoints": [[190, 0.30], [200, 0.85], [204, 0.95], [210, 0.60], [220, 0.35], [230, 0.20], [240, 0.32], [248, 0.60], [252, 0.78], [255, 0.82], [258, 0.70], [262, 0.45], [270, 0.18], [280, 0.08], [290, 0.05], [300, 0.02], [320, 0.01], [350, 0], [380, 0], [400, 0]]
            }
        ]
    },
    {
        "picId": 6,
        "spectra": [
            {
                "id": "spec-6-ir", "type": "IR", "name": "Ammonia FTIR Spectrum", "instrument": "Bruker VERTEX 70", "conditions": "Gas cell, 400-4000 cm⁻¹, RT", "xLabel": "Wavenumber (cm⁻¹)", "yLabel": "Transmittance (%)",
                "peaks": [{"x": 3336, "y": 70, "label": "N-H stretch (asym)"}, {"x": 1628, "y": 55, "label": "H-N-H bend (asym)"}, {"x": 950, "y": 48, "label": "N-H bend (sym)"}],
                "dataPoints": [[400, 90], [600, 82], [800, 55], [950, 48], [1100, 60], [1300, 68], [1500, 52], [1628, 55], [1800, 72], [2000, 80], [2200, 85], [2400, 88], [2600, 84], [2800, 78], [3000, 72], [3200, 65], [3336, 70], [3500, 55], [3700, 40], [4000, 35]]
            },
            {
                "id": "spec-6-raman", "type": "Raman", "name": "Ammonia Raman Spectrum", "instrument": "Horiba LabRAM HR", "conditions": "532 nm laser, 100-4000 cm⁻¹, RT", "xLabel": "Raman Shift (cm⁻¹)", "yLabel": "Intensity (a.u.)",
                "peaks": [{"x": 3334, "y": 88, "label": "N-H stretch"}, {"x": 950, "y": 62, "label": "Symmetric deformation"}],
                "dataPoints": [[100, 5], [300, 8], [500, 10], [700, 18], [900, 55], [950, 62], [1000, 35], [1200, 12], [1500, 10], [1800, 8], [2000, 15], [2400, 10], [2800, 20], [3000, 35], [3200, 70], [3334, 88], [3500, 40], [3700, 15], [4000, 8]]
            }
        ]
    }
]

mock_category_summary = [
    {"category": "无机小分子", "count": 2341, "percentage": 18.8},
    {"category": "有机小分子", "count": 4521, "percentage": 36.3},
    {"category": "芳香族化合物", "count": 1876, "percentage": 15.1},
    {"category": "无机盐", "count": 1203, "percentage": 9.7},
    {"category": "烯烃", "count": 892, "percentage": 7.2},
    {"category": "无机酸", "count": 523, "percentage": 4.2},
    {"category": "过渡金属配合物", "count": 678, "percentage": 5.4},
    {"category": "其他", "count": 422, "percentage": 3.4}
]

mock_molecule_summary = [
    {"id": 1, "title": "小分子化合物数据库概述", "description": "涵盖常见无机和有机小分子的结构、性质和谱学数据，包含IR、NMR、MS等多维表征信息。", "category": "organic", "updateTime": "2026-06-10"},
    {"id": 2, "title": "过渡金属催化剂数据集", "description": "包含Fe、Co、Ni、Cu、Pd、Pt等多种过渡金属的催化体系数据，涵盖均相和异相催化反应。", "category": "catalyst", "updateTime": "2026-05-28"},
    {"id": 3, "title": "芳香族化合物光谱合集", "description": "收录苯系、萘系、杂环芳香族化合物的IR、NMR、MS、UV-Vis谱图数据。", "category": "spectra", "updateTime": "2026-06-01"},
    {"id": 4, "title": "计算化学基准数据集", "description": "基于DFT计算的分子结构优化、频率分析和热力学数据，包含多种泛函和基组水平计算结果。", "category": "computational", "updateTime": "2026-05-15"},
    {"id": 5, "title": "谱学标准参考数据集", "description": "收录常见官能团和化合物的标准谱图数据，用于谱图解析和结构鉴定参考。", "category": "spectra", "updateTime": "2026-04-20"}
]

mock_obs_files = [
    {"id": "obs-001", "name": "h2o_spectrum_raw.fid", "size": 2457600, "type": "application/octet-stream", "uploadTime": "2026-06-01 10:30:00", "moleculeId": 1, "description": "H₂O NMR raw FID data (Bruker format)"},
    {"id": "obs-002", "name": "benzene_ftir.dpt", "size": 102400, "type": "application/octet-stream", "uploadTime": "2026-05-15 14:20:00", "moleculeId": 4, "description": "Benzene FTIR data file (Thermo format)"},
    {"id": "obs-003", "name": "ethanol_ms_spectrum.mzML", "size": 5120000, "type": "application/xml", "uploadTime": "2026-05-20 09:15:00", "moleculeId": 3, "description": "Ethanol GC-MS spectrum in mzML format"},
    {"id": "obs-004", "name": "ammonia_raman.spc", "size": 81920, "type": "application/octet-stream", "uploadTime": "2026-04-05 16:45:00", "moleculeId": 6, "description": "Ammonia Raman spectrum (GRAMS SPC format)"},
    {"id": "obs-005", "name": "water_optimization.chk", "size": 8388608, "type": "application/octet-stream", "uploadTime": "2026-06-08 11:00:00", "moleculeId": 1, "description": "H₂O DFT optimization checkpoint file (Gaussian)"},
    {"id": "obs-006", "name": "benzene_crystal.cif", "size": 5120, "type": "chemical/x-cif", "uploadTime": "2026-05-30 08:30:00", "moleculeId": 4, "description": "Benzene crystal structure CIF file"}
]

mock_spectrum_types = [
    {"type": "IR", "label": "红外光谱 (IR)", "count": 4520},
    {"type": "NMR", "label": "核磁共振 (NMR)", "count": 3800},
    {"type": "MS", "label": "质谱 (MS)", "count": 5100},
    {"type": "Raman", "label": "拉曼光谱 (Raman)", "count": 1200},
    {"type": "UV-Vis", "label": "紫外-可见 (UV-Vis)", "count": 2300},
    {"type": "XRD", "label": "X射线衍射 (XRD)", "count": 890}
]
# =============== 插入数据方法 ===============

def insert_users(db_path='chemistry.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT OR IGNORE INTO users (id, username, password, email, role, nickname, phone, avatar, createTime)
            VALUES (:id, :username, :password, :email, :role, :nickname, :phone, :avatar, :createTime)
        ''', mock_users)
        conn.commit()

def insert_news(db_path='chemistry.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT OR IGNORE INTO news (id, title, content, author, summary, createTime)
            VALUES (:id, :title, :content, :author, :summary, :createTime)
        ''', mock_news)
        conn.commit()

def insert_announcements(db_path='chemistry.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT OR IGNORE INTO announcements (id, title, content, author, importance, createTime)
            VALUES (:id, :title, :content, :author, :importance, :createTime)
        ''', mock_announcements)
        conn.commit()

def insert_molecules(db_path='chemistry.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for m in mock_molecules:
            cursor.execute('''
                INSERT OR IGNORE INTO molecules 
                (id, formula, smiles, inchi, mass, volume, type, tags, charge, spin, atoms, bonds, createTime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                m.get('id'), m.get('formula'), m.get('smiles'), m.get('inchi'),
                m.get('mass'), m.get('volume'), m.get('type'),
                json.dumps(m.get('tags', [])),  # 处理数组
                m.get('charge'), m.get('spin'),
                json.dumps(m.get('atoms', [])), # 处理数组
                json.dumps(m.get('bonds', [])), # 处理数组
                m.get('createTime')
            ))
        conn.commit()

def insert_materials(db_path='chemistry.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for m in mock_materials:
            cursor.execute('''
                INSERT OR IGNORE INTO materials 
                (id, name, formula, type, tags, bandGap, latticeConstant, crystalSystem, spaceGroup, createTime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                m.get('id'), m.get('name'), m.get('formula'), m.get('type'),
                json.dumps(m.get('tags', [])),  # 处理数组
                m.get('bandGap'), m.get('latticeConstant'),
                m.get('crystalSystem'), m.get('spaceGroup'),
                m.get('createTime')
            ))
        conn.commit()

def insert_literature(db_path='chemistry.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for l in mock_literature:
            cursor.execute('''
                INSERT OR IGNORE INTO literature 
                (id, doi, title, authors, journal, year, volume, issue, pages, abstract, keywords, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                l.get('id'), l.get('doi'), l.get('title'), l.get('authors'),
                l.get('journal'), l.get('year'), l.get('volume'), l.get('issue'),
                l.get('pages'), l.get('abstract'),
                json.dumps(l.get('keywords', [])), # 处理数组
                json.dumps(l.get('tags', []))      # 处理数组
            ))
        conn.commit()

def insert_molecule_tags(db_path='chemistry.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT OR IGNORE INTO molecule_tags (id, name, count, category)
            VALUES (:id, :name, :count, :category)
        ''', mock_molecule_tags)
        conn.commit()

def insert_material_tags(db_path='chemistry.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT OR IGNORE INTO material_tags (id, name, count, category)
            VALUES (:id, :name, :count, :category)
        ''', mock_material_tags)
        conn.commit()
    
def insert_audit_logs(db_path='chemistry.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT OR IGNORE INTO audit_logs (id, userId, username, action, resource, detail, ip, time)
            VALUES (:id, :userId, :username, :action, :resource, :detail, :ip, :time)
        ''', mock_audit_logs)
        conn.commit()

def insert_metadata(db_path='chemistry.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT OR IGNORE INTO metadata (id, fieldEn, fieldZh, type, required, description)
            VALUES (:id, :fieldEn, :fieldZh, :type, :required, :description)
        ''', mock_metadata)
        conn.commit()

def insert_spectrum(db_path='chemistry.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # 展平嵌套的光谱数据结构
        flattened_spectra = []
        for item in mock_spectrum:
            pic_id = item.get('picId')
            for spec in item.get('spectra', []):
                flattened_spectra.append({
                    'id': spec.get('id'),
                    'picId': pic_id,
                    'type': spec.get('type'),
                    'name': spec.get('name'),
                    'instrument': spec.get('instrument'),
                    'conditions': spec.get('conditions'),
                    'xLabel': spec.get('xLabel'),
                    'yLabel': spec.get('yLabel'),
                    'peaks': json.dumps(spec.get('peaks', [])),           # 数组转JSON字符串
                    'dataPoints': json.dumps(spec.get('dataPoints', []))  # 数组转JSON字符串
                })
        
        cursor.executemany('''
            INSERT OR IGNORE INTO spectrum (id, picId, type, name, instrument, conditions, xLabel, yLabel, peaks, dataPoints)
            VALUES (:id, :picId, :type, :name, :instrument, :conditions, :xLabel, :yLabel, :peaks, :dataPoints)
        ''', flattened_spectra)
        conn.commit()

def insert_category_summary(db_path='chemistry.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        # mock_category_summary 数据中没有提供 id，利用 AUTOINCREMENT 自动生成
        cursor.executemany('''
            INSERT OR IGNORE INTO category_summary (category, count, percentage)
            VALUES (:category, :count, :percentage)
        ''', mock_category_summary)
        conn.commit()

def insert_molecule_summary(db_path='chemistry.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT OR IGNORE INTO molecule_summary (id, title, description, category, updateTime)
            VALUES (:id, :title, :description, :category, :updateTime)
        ''', mock_molecule_summary)
        conn.commit()

def insert_obs_files(db_path='chemistry.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT OR IGNORE INTO obs_files (id, name, size, type, uploadTime, moleculeId, description)
            VALUES (:id, :name, :size, :type, :uploadTime, :moleculeId, :description)
        ''', mock_obs_files)
        conn.commit()

def insert_spectrum_types(db_path='chemistry.db'):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        # 数据中同样未提供 id
        cursor.executemany('''
            INSERT OR IGNORE INTO spectrum_types (type, label, count)
            VALUES (:type, :label, :count)
        ''', mock_spectrum_types)
        conn.commit()

# 一键执行所有插入
def insert_all_mock_data(db_path='chemistry.db'):
    insert_users(db_path)
    insert_news(db_path)
    insert_announcements(db_path)
    insert_molecules(db_path)
    insert_materials(db_path)
    insert_literature(db_path)
    insert_molecule_tags(db_path)
    insert_material_tags(db_path)
    insert_audit_logs(db_path)
    insert_metadata(db_path)
    insert_spectrum(db_path)
    insert_category_summary(db_path)
    insert_molecule_summary(db_path)
    insert_obs_files(db_path)
    insert_spectrum_types(db_path)

if __name__ == "__main__":
    import os
    import tomli
    parent_dir = Path(__file__).resolve().parent.parent
    os.chdir(parent_dir)
    with open(parent_dir / "config" / "config.toml", "rb") as f:
        config = tomli.load(f)
    db_path = config["database"]["path"]
    db_path = db_path + 'chemistry.db'
    insert_all_mock_data(db_path)