#!/usr/bin/env python3
"""
AI简历优化Agent - 单文件Python实现
======================================
功能: 输入JD+简历 → 自动解析 → 匹配度评分 → 智能优化 → 输出优化后简历+建议
技术: 纯Python标准库 + json，不依赖任何LLM API，使用内置模板引擎+规则引擎模拟Agent工作流

Author: Portfolio Project
Version: 1.0.0
"""

import json
import re
import sys
from typing import Dict, List, Tuple, Optional


# ==============================================================================
# 预设数据
# ==============================================================================

PRESET_JD_1 = """
高级Python后端工程师
公司名称：某知名互联网公司
工作地点：北京/上海
薪资：30-50K

岗位职责：
1. 负责公司核心产品的后端架构设计与开发
2. 设计和优化高并发、高可用的分布式系统
3. 参与技术方案评审，推动技术选型和架构演进
4. 指导初中级工程师，进行Code Review

任职要求：
1. 本科及以上学历，计算机相关专业优先
2. 5年以上Python后端开发经验
3. 精通Django/Flask/FastAPI等Web框架
4. 熟悉MySQL、PostgreSQL等关系型数据库
5. 精通Redis、消息队列（Kafka/RabbitMQ）
6. 熟悉Docker、Kubernetes容器化技术
7. 有微服务架构设计和实践经验
8. 熟悉CI/CD流程，了解DevOps理念
9. 良好的系统设计能力和问题排查能力
10. 有大数据处理经验（Spark/Hadoop）优先
"""

PRESET_RESUME_1 = """
张三
手机：138-0000-0000
邮箱：zhangsan@email.com
求职意向：Python后端工程师

教育背景：
浙江大学 计算机科学与技术 本科 2017-2021

工作经历：
杭州某科技公司 | Python开发工程师 | 2021.07-至今
- 参与公司电商平台后端开发，使用Django框架
- 负责用户模块、订单模块的接口开发和维护
- 使用MySQL数据库，编写SQL查询和存储过程
- 使用Redis做缓存，优化接口响应时间
- 参与微服务拆分项目，使用Docker部署服务

项目经历：
1. 电商订单系统重构
   - 将原有单体架构拆分为微服务
   - 使用Docker容器化部署
   - 优化数据库查询，接口响应时间提升40%

2. 用户行为分析平台
   - 使用Flask开发后端API
   - 数据存储在PostgreSQL
   - 使用Celery处理异步任务

技能：
Python, Django, Flask, MySQL, Redis, Docker, Linux, Git, RESTful API
"""

PRESET_JD_2 = """
数据分析师
公司名称：某金融科技公司
工作地点：深圳
薪资：20-35K

岗位职责：
1. 负责业务数据的分析和挖掘
2. 建立数据分析模型，为业务决策提供支持
3. 设计和优化数据报表和数据可视化
4. 与产品、运营团队协作，推动数据驱动决策

任职要求：
1. 本科及以上学历，统计学/数学/计算机相关专业
2. 3年以上数据分析相关工作经验
3. 精通SQL，熟悉Python/R数据分析
4. 熟练使用Pandas、NumPy等数据分析库
5. 熟悉数据可视化工具（Matplotlib/Tableau/PowerBI）
6. 有机器学习实践经验优先
7. 良好的业务理解能力和沟通能力
8. 金融行业数据分析经验优先
"""

PRESET_RESUME_2 = """
李四
手机：139-0000-0000
邮箱：lisi@email.com
求职意向：数据分析师

教育背景：
中山大学 统计学 硕士 2019-2022

工作经历：
深圳某互联网公司 | 数据运营专员 | 2022.07-至今
- 负责日常数据报表的制作和维护
- 使用Excel和SQL进行数据查询和统计
- 协助分析师完成用户行为分析报告
- 使用Python编写简单的数据清洗脚本
- 参与AB测试方案设计和效果分析

项目经历：
1. 用户留存分析报告
   - 使用SQL查询用户行为数据
   - 用Excel制作可视化图表
   - 输出分析报告，为产品迭代提供建议

2. 营销活动效果评估
   - 设计数据采集方案
   - 使用Python Pandas进行数据整理
   - 制作数据看板展示活动效果

技能：
SQL, Excel, Python基础, Pandas, 数据分析, 数据报表, 统计学
"""


# ==============================================================================
# 步骤1: JD解析器
# ==============================================================================

class JDParser:
    """JD解析器：从JD文本中提取结构化信息"""
    
    # 技术关键词库
    TECH_SKILLS = [
        "python", "java", "javascript", "typescript", "go", "c++", "ruby",
        "django", "flask", "fastapi", "spring", "react", "vue", "angular",
        "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "docker", "kubernetes", "k8s", "aws", "azure", "gcp",
        "kafka", "rabbitmq", "spark", "hadoop", "hadoop",
        "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
        "machine learning", "deep learning", "nlp", "cv",
        "ci/cd", "devops", "git", "linux", "jenkins",
        "microservice", "micro-service", "微服务",
        "sql", "nosql", "restful", "rest api",
        "tableau", "powerbi", "power bi", "matplotlib",
        "r语言", "r ", "统计学",
    ]
    
    # 经验年限模式
    EXPERIENCE_PATTERNS = [
        r"(\d+)\s*年.*经验",
        r"(\d+)\s*年以上",
        r"经验.*?(\d+)\s*年",
    ]
    
    # 学历关键词
    EDUCATION_LEVELS = ["博士", "硕士", "本科", "大专", "学士"]
    
    @staticmethod
    def parse(jd_text: str) -> Dict:
        """解析JD文本，返回结构化数据"""
        text_lower = jd_text.lower()
        
        # 提取技能关键词
        skills = JDParser._extract_skills(text_lower)
        
        # 提取经验要求
        experience = JDParser._extract_experience(jd_text)
        
        # 提取学历要求
        education = JDParser._extract_education(jd_text)
        
        # 提取职位标题
        title = JDParser._extract_title(jd_text)
        
        return {
            "title": title,
            "required_skills": skills,
            "experience_years": experience,
            "education_required": education,
            "raw_text": jd_text.strip(),
        }
    
    @staticmethod
    def _extract_skills(text_lower: str) -> List[str]:
        """从JD中提取技能关键词"""
        found_skills = []
        for skill in JDParser.TECH_SKILLS:
            # 使用词边界匹配，避免子串误匹配
            pattern = r'\b' + re.escape(skill) + r'\b' if skill.isascii() else re.escape(skill)
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        return list(set(found_skills))  # 去重
    
    @staticmethod
    def _extract_experience(text: str) -> int:
        """提取经验年限要求"""
        for pattern in JDParser.EXPERIENCE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return 0
    
    @staticmethod
    def _extract_education(text: str) -> str:
        """提取学历要求"""
        for level in JDParser.EDUCATION_LEVELS:
            if level in text:
                return level
        return ""
    
    @staticmethod
    def _extract_title(text: str) -> str:
        """提取职位标题（通常在前几行）"""
        lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
        if lines:
            # 取第一行非空且较短的行作为标题
            for line in lines[:5]:
                if len(line) < 50 and '公司' not in line and '地点' not in line:
                    return line
        return "未知职位"


# ==============================================================================
# 步骤2: 简历解析器
# ==============================================================================

class ResumeParser:
    """简历解析器：从简历文本中提取结构化信息"""
    
    # 扩展的技能识别库
    RESUME_SKILLS = [
        "python", "java", "javascript", "go", "sql", "r",
        "django", "flask", "fastapi", "spring", "react", "vue",
        "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "docker", "kubernetes", "k8s", "aws",
        "kafka", "rabbitmq", "spark", "hadoop",
        "pandas", "numpy", "scikit-learn", "matplotlib",
        "tableau", "powerbi", "celery", "linux", "git",
        "restful", "rest api", "microservice", "微服务",
        "ci/cd", "devops", "excel", "数据清洗", "数据分析",
        "machine learning", "deep learning", "statistics", "统计学",
        "html", "css", "react", "nodejs", "mongodb",
    ]
    
    @staticmethod
    def parse(resume_text: str) -> Dict:
        """解析简历文本，返回结构化数据"""
        text_lower = resume_text.lower()
        
        # 提取姓名
        name = ResumeParser._extract_name(resume_text)
        
        # 提取技能
        skills = ResumeParser._extract_skills(text_lower)
        
        # 提取教育背景
        education = ResumeParser._extract_education(resume_text)
        
        # 估算工作年限
        years = ResumeParser._estimate_experience(resume_text)
        
        # 提取项目经历数量
        project_count = ResumeParser._count_projects(resume_text)
        
        return {
            "name": name,
            "skills": skills,
            "education": education,
            "experience_years": years,
            "project_count": project_count,
            "raw_text": resume_text.strip(),
        }
    
    @staticmethod
    def _extract_name(text: str) -> str:
        """提取姓名"""
        lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
        # 姓名通常在第一行，且较短
        if lines:
            first_line = lines[0]
            # 过滤掉明显不是姓名的行
            if len(first_line) <= 10 and not re.search(r'[\d@]', first_line):
                return first_line
        return "未知"
    
    @staticmethod
    def _extract_skills(text_lower: str) -> List[str]:
        """从简历中提取技能"""
        found_skills = []
        for skill in ResumeParser.RESUME_SKILLS:
            pattern = r'\b' + re.escape(skill) + r'\b' if skill.isascii() else re.escape(skill)
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        return list(set(found_skills))
    
    @staticmethod
    def _extract_education(text: str) -> Dict:
        """提取教育背景"""
        edu_info = {"degree": "", "school": "", "major": ""}
        
        # 学历
        for degree in ["博士", "硕士", "本科", "大专", "学士"]:
            if degree in text:
                edu_info["degree"] = degree
                break
        
        # 学校（常见高校关键词）
        schools = ["大学", "学院", "university", "college"]
        for line in text.split('\n'):
            for school_keyword in schools:
                if school_keyword in line.lower():
                    edu_info["school"] = line.strip().split()[0] if line.strip() else ""
                    # 提取更完整的学校名
                    match = re.search(r'([\u4e00-\u9fa5]{2,10}(?:大学|学院))', line)
                    if match:
                        edu_info["school"] = match.group(1)
                    break
        
        # 专业
        majors = ["计算机", "软件", "统计学", "数学", "信息", "电子", "自动化", "数据科学"]
        for major in majors:
            if major in text:
                edu_info["major"] = major
                break
        
        return edu_info
    
    @staticmethod
    def _estimate_experience(text: str) -> float:
        """根据工作经历中的时间估算工作年限"""
        # 查找年份范围
        year_ranges = re.findall(r'20\d{2}[\.\-/年]?\s*(?:\d{1,2})?\s*[-–~至到]\s*(?:20\d{2}|至今|现在|今)', text)
        if year_ranges:
            max_years = 0
            for r in year_ranges:
                years = re.findall(r'20\d{2}', r)
                if len(years) >= 2:
                    start_year = int(years[0])
                    end_str = years[1]
                    end_year = int(end_str) if end_str not in ['至今', '现在', '今'] else 2025
                    duration = end_year - start_year
                    max_years = max(max_years, duration)
            return float(max_years)
        
        # 如果找不到时间范围，尝试找"X年经验"
        match = re.search(r'(\d+)\s*年.*经验', text)
        if match:
            return float(match.group(1))
        
        return 0.0
    
    @staticmethod
    def _count_projects(text: str) -> int:
        """计算项目经历数量"""
        # 通过编号或"项目"关键词计数
        project_matches = re.findall(r'(?:项目经历|项目经验).*?(?=\n\S|\Z)', text, re.DOTALL)
        if project_matches:
            # 计算项目数（通过数字编号或"项目"关键词）
            project_section = project_matches[0]
            numbered = re.findall(r'\d+[\.\、\)]', project_section)
            return max(len(numbered), 1)
        return 0


# ==============================================================================
# 步骤3: 匹配度计算引擎
# ==============================================================================

class MatchEngine:
    """匹配度计算引擎：多维度评分"""
    
    @staticmethod
    def calculate(jd_parsed: Dict, resume_parsed: Dict) -> Dict:
        """计算JD与简历的匹配度"""
        
        # 维度1: 技能覆盖率 (0-40分)
        skill_score, skill_details = MatchEngine._skill_match_score(
            jd_parsed["required_skills"], resume_parsed["skills"]
        )
        
        # 维度2: 经验匹配度 (0-25分)
        exp_score, exp_details = MatchEngine._experience_match_score(
            jd_parsed["experience_years"], resume_parsed["experience_years"]
        )
        
        # 维度3: 学历匹配度 (0-15分)
        edu_score, edu_details = MatchEngine._education_match_score(
            jd_parsed["education_required"], resume_parsed["education"]
        )
        
        # 维度4: 项目经历丰富度 (0-10分)
        project_score = MatchEngine._project_score(resume_parsed["project_count"])
        
        # 维度5: 技能相关度加分 (0-10分)
        relevance_score = MatchEngine._relevance_bonus(
            jd_parsed["required_skills"], resume_parsed["skills"]
        )
        
        total_score = skill_score + exp_score + edu_score + project_score + relevance_score
        total_score = min(100, max(0, total_score))
        
        return {
            "total_score": total_score,
            "score_level": MatchEngine._get_level(total_score),
            "breakdown": {
                "skill_coverage": {"score": skill_score, "max": 40, "details": skill_details},
                "experience_match": {"score": exp_score, "max": 25, "details": exp_details},
                "education_match": {"score": edu_score, "max": 15, "details": edu_details},
                "project_richness": {"score": project_score, "max": 10},
                "skill_relevance": {"score": relevance_score, "max": 10},
            },
            "matched_skills": skill_details["matched"],
            "missing_skills": skill_details["missing"],
        }
    
    @staticmethod
    def _skill_match_score(required: List[str], candidate: List[str]) -> Tuple[int, Dict]:
        """计算技能覆盖率得分"""
        if not required:
            return 20, {"matched": [], "missing": [], "rate": 0}
        
        required_set = set(s.lower() for s in required)
        candidate_set = set(s.lower() for s in candidate)
        
        matched = required_set & candidate_set
        missing = required_set - candidate_set
        
        rate = len(matched) / len(required_set) if required_set else 0
        score = int(rate * 40)
        
        return score, {
            "matched": sorted(list(matched)),
            "missing": sorted(list(missing)),
            "rate": round(rate * 100, 1),
        }
    
    @staticmethod
    def _experience_match_score(required: int, candidate: float) -> Tuple[int, Dict]:
        """计算经验匹配度得分"""
        if required == 0:
            return 15, {"required": 0, "actual": candidate, "status": "无明确要求"}
        
        if candidate >= required:
            score = 25
            status = "满足"
        elif candidate >= required * 0.7:
            score = 18
            status = "略低于要求"
        elif candidate >= required * 0.5:
            score = 12
            status = "低于要求"
        else:
            score = 5
            status = "显著低于要求"
        
        return score, {
            "required": required,
            "actual": candidate,
            "gap": max(0, required - candidate),
            "status": status,
        }
    
    @staticmethod
    def _education_match_score(required: str, candidate: Dict) -> Tuple[int, Dict]:
        """计算学历匹配度得分"""
        if not required:
            return 10, {"status": "无明确要求"}
        
        degree_hierarchy = {"博士": 4, "硕士": 3, "本科": 2, "大专": 1, "学士": 2}
        
        req_level = degree_hierarchy.get(required, 0)
        cand_degree = candidate.get("degree", "")
        cand_level = degree_hierarchy.get(cand_degree, 0)
        
        if cand_level >= req_level:
            score = 15
            status = "满足"
        elif cand_level == req_level - 1:
            score = 10
            status = "略低于要求"
        else:
            score = 5
            status = "低于要求"
        
        return score, {
            "required": required,
            "actual": cand_degree,
            "status": status,
        }
    
    @staticmethod
    def _project_score(count: int) -> int:
        """项目经历丰富度评分"""
        if count >= 3:
            return 10
        elif count >= 2:
            return 7
        elif count >= 1:
            return 4
        return 2
    
    @staticmethod
    def _relevance_bonus(required: List[str], candidate: List[str]) -> int:
        """技能相关度加分：相近技能也给予部分分数"""
        # 定义技能关联组
        skill_groups = [
            {"django", "flask", "fastapi", "spring", "express"},
            {"mysql", "postgresql", "mongodb", "redis"},
            {"kafka", "rabbitmq", "rocketmq"},
            {"pandas", "numpy", "scipy"},
            {"docker", "kubernetes", "k8s"},
            {"tensorflow", "pytorch", "scikit-learn"},
        ]
        
        candidate_set = set(s.lower() for s in candidate)
        bonus = 0
        
        for group in skill_groups:
            required_in_group = group & set(s.lower() for s in required)
            candidate_in_group = group & candidate_set
            if required_in_group and candidate_in_group:
                # JD要求的技能组中，候选人有该组中的其他技能
                extra = candidate_in_group - required_in_group
                if extra:
                    bonus += min(3, len(extra))
        
        return min(10, bonus)
    
    @staticmethod
    def _get_level(score: int) -> str:
        """根据总分返回匹配等级"""
        if score >= 85:
            return "高度匹配 (A)"
        elif score >= 70:
            return "较好匹配 (B)"
        elif score >= 55:
            return "一般匹配 (C)"
        elif score >= 40:
            return "部分匹配 (D)"
        else:
            return "匹配度较低 (E)"


# ==============================================================================
# 步骤4: 简历优化引擎
# ==============================================================================

class ResumeOptimizer:
    """简历优化引擎：基于匹配结果生成优化建议和改进后的简历"""
    
    @staticmethod
    def optimize(jd_parsed: Dict, resume_parsed: Dict, match_result: Dict) -> Dict:
        """执行简历优化，返回优化建议和优化后的简历"""
        
        # 生成优化建议
        suggestions = ResumeOptimizer._generate_suggestions(jd_parsed, resume_parsed, match_result)
        
        # 生成优化后的简历文本
        optimized_text = ResumeOptimizer._generate_optimized_resume(
            jd_parsed, resume_parsed, match_result, suggestions
        )
        
        # 生成关键优化摘要
        highlights = ResumeOptimizer._generate_highlights(match_result, suggestions)
        
        return {
            "suggestions": suggestions,
            "optimized_resume": optimized_text,
            "highlights": highlights,
        }
    
    @staticmethod
    def _generate_suggestions(jd_parsed: Dict, resume_parsed: Dict, match_result: Dict) -> List[Dict]:
        """基于匹配分析生成具体优化建议"""
        suggestions = []
        breakdown = match_result["breakdown"]
        
        # 1. 缺失技能建议
        missing_skills = match_result.get("missing_skills", [])
        if missing_skills:
            priority = "高" if len(missing_skills) <= 3 else "中"
            suggestions.append({
                "category": "技能补充",
                "priority": priority,
                "issue": f"缺少JD要求的关键技能: {', '.join(missing_skills[:5])}",
                "action": f"建议在简历中突出学习或接触过的相关技术。如果是{missing_skills[0]}，可以描述相关项目经验或自学成果。",
                "impact": "直接影响简历筛选通过率",
            })
        
        # 2. 经验差距建议
        exp_detail = breakdown["experience_match"]["details"]
        if exp_detail.get("status") not in ["满足", "无明确要求"]:
            gap = exp_detail.get("gap", 0)
            suggestions.append({
                "category": "经验呈现",
                "priority": "高",
                "issue": f"工作经验与JD要求有{gap}年差距（要求{exp_detail.get('required')}年，当前约{exp_detail.get('actual')}年）",
                "action": "建议在项目描述中突出技术深度和复杂度，用量化数据展示成果。强调独立负责模块的能力和解决复杂问题的经验。",
                "impact": "弥补年限差距，展示实际能力",
            })
        
        # 3. 技能表述优化
        skill_rate = breakdown["skill_coverage"]["details"].get("rate", 0)
        if skill_rate < 70:
            suggestions.append({
                "category": "技能描述优化",
                "priority": "高",
                "issue": f"技能关键词覆盖率仅{skill_rate}%，简历可能无法通过ATS系统筛选",
                "action": '建议在工作经历和项目描述中自然嵌入更多JD中的关键词，如"使用' + ', '.join(match_result.get('matched_skills', [])[:2]) + '实现..."。同时补充缺失但相关的技能。',
                "impact": "提升ATS系统通过率",
            })
        
        # 4. 项目经历优化
        if breakdown["project_richness"]["score"] < 7:
            suggestions.append({
                "category": "项目经历丰富",
                "priority": "中",
                "issue": "项目经历数量偏少，无法充分展示技术广度",
                "action": "建议补充个人项目、开源贡献或技术实践。可以从工作中的小功能点提炼为独立项目描述，使用STAR法则（情境-任务-行动-结果）组织内容。",
                "impact": "增加面试邀约概率",
            })
        
        # 5. 量化成果建议
        suggestions.append({
            "category": "成果量化",
            "priority": "中",
            "issue": "简历中缺少量化数据支撑",
            "action": "建议为每个项目添加量化指标，如：系统QPS提升了X倍、接口响应时间降低X%、服务可用性达到99.X%、处理数据量达X级别等。",
            "impact": "让面试官直观感知你的业务价值",
        })
        
        # 6. 学历相关建议
        edu_detail = breakdown["education_match"]["details"]
        if edu_detail.get("status") == "低于要求":
            suggestions.append({
                "category": "学历补充",
                "priority": "低",
                "issue": f"学历要求{edu_detail.get('required')}，当前学历可能不满足",
                "action": "建议突出教育背景中的亮点（如GPA、奖学金、相关课程），或通过在线课程证书、技术认证来补充。",
                "impact": "减少学历筛选环节的劣势",
            })
        
        # 按优先级排序
        priority_order = {"高": 0, "中": 1, "低": 2}
        suggestions.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return suggestions
    
    @staticmethod
    def _generate_optimized_resume(jd_parsed: Dict, resume_parsed: Dict,
                                    match_result: Dict, suggestions: List[Dict]) -> str:
        """生成优化后的简历文本"""
        name = resume_parsed["name"]
        
        # 构建优化后的技能列表
        original_skills = resume_parsed["skills"]
        matched_skills = match_result.get("matched_skills", [])
        missing_skills = match_result.get("missing_skills", [])
        
        # 将缺失技能中的相关技能以"了解/熟悉"的程度加入
        all_skills = list(set(original_skills))
        # 将匹配的技能排在前面
        skill_display = []
        for s in matched_skills:
            if s in all_skills:
                skill_display.append(s)
        for s in all_skills:
            if s not in matched_skills:
                skill_display.append(s)
        # 添加缺失技能作为"学习中"
        learning_skills = missing_skills[:3]  # 最多加3个
        
        lines = []
        lines.append(f"{'='*60}")
        lines.append(f"  {name} - 优化版简历")
        lines.append(f"  目标职位: {jd_parsed['title']}")
        lines.append(f"{'='*60}")
        lines.append("")
        
        # 个人总结（新增优化项）
        lines.append("【个人总结】（建议新增）")
        years = resume_parsed["experience_years"]
        lines.append(f"  {years}年Python后端开发经验，熟悉{', '.join(matched_skills[:4])}等技术栈。")
        lines.append(f"  具备微服务架构设计经验，有高并发系统优化实践。")
        if learning_skills:
            lines.append(f"  目前正在深入学习{'、'.join(learning_skills)}，持续拓展技术视野。")
        lines.append("")
        
        # 技能清单（优化排列）
        lines.append("【核心技能】（优化关键词顺序和覆盖度）")
        skill_categories = {
            "编程语言": ["python", "java", "javascript", "go", "sql", "r"],
            "框架/库": ["django", "flask", "fastapi", "pandas", "numpy", "celery", "matplotlib"],
            "数据库": ["mysql", "postgresql", "mongodb", "redis", "elasticsearch"],
            "工具/平台": ["docker", "kubernetes", "k8s", "git", "linux", "aws", "kafka", "rabbitmq"],
        }
        for category, cat_skills in skill_categories.items():
            matched = [s for s in cat_skills if s in set(skill_display)]
            if matched:
                lines.append(f"  {category}: {' / '.join(s.upper() for s in matched)}")
        if learning_skills:
            lines.append(f"  学习中: {' / '.join(s.upper() for s in learning_skills)}")
        lines.append("")
        
        # 工作经历优化建议
        lines.append("【工作经历】（优化建议：按STAR法则改写）")
        lines.append("  建议改写示例：")
        lines.append("  优化前：负责用户模块的接口开发和维护")
        lines.append("  优化后：独立负责用户中心模块（覆盖注册/登录/权限管理），")
        lines.append("         使用Django REST Framework开发20+API接口，日均请求量10W+，")
        lines.append("         接口P99延迟从500ms优化至120ms")
        lines.append("")
        
        # 项目经历优化建议
        lines.append("【项目经历】（优化建议：突出量化成果和技术难点）")
        lines.append("  建议改写示例：")
        lines.append("  项目名称：电商订单系统微服务重构")
        lines.append("  技术栈：Python + Django + Docker + MySQL + Redis + Kafka")
        lines.append("  项目描述：将单体架构拆分为6个微服务，提升系统可扩展性")
        lines.append("  核心贡献：")
        lines.append("    - 设计服务间通信方案，使用Kafka实现异步消息解耦")
        lines.append("    - 优化数据库查询，核心接口响应时间降低40%")
        lines.append("    - 基于Docker实现容器化部署，支持一键扩缩容")
        lines.append("    - 系统上线后支撑日均100W+订单处理，可用性99.9%")
        lines.append("")
        
        # ATS优化提示
        lines.append("【ATS优化提示】")
        lines.append(f"  当前关键词覆盖率: {match_result['breakdown']['skill_coverage']['details'].get('rate', 0)}%")
        lines.append(f"  建议补充关键词: {', '.join(missing_skills[:5]) if missing_skills else '无明显缺失'}")
        lines.append(f"  优化后预计覆盖率: {min(95, match_result['breakdown']['skill_coverage']['details'].get('rate', 0) + 20)}%")
        lines.append("")
        lines.append(f"{'='*60}")
        lines.append("  注：以上为AI优化建议，请根据个人实际情况调整内容")
        lines.append(f"{'='*60}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def _generate_highlights(match_result: Dict, suggestions: List[Dict]) -> List[str]:
        """生成关键优化摘要"""
        highlights = []
        
        score = match_result["total_score"]
        if score < 60:
            highlights.append(f"当前匹配度{score}分，建议重点补充缺失技能和量化成果")
        elif score < 80:
            highlights.append(f"当前匹配度{score}分，基础较好，重点优化项目描述的量化表达")
        else:
            highlights.append(f"当前匹配度{score}分，匹配度较高，建议精修细节以脱颖而出")
        
        high_priority = [s for s in suggestions if s["priority"] == "高"]
        if high_priority:
            highlights.append(f"有{len(high_priority)}项高优先级优化建议需要重点关注")
        
        missing_count = len(match_result.get("missing_skills", []))
        if missing_count > 0:
            highlights.append(f"需要补充{missing_count}项JD要求的关键技能")
        
        return highlights


# ==============================================================================
# 步骤5: 报告生成器
# ==============================================================================

class ReportGenerator:
    """报告生成器：输出结构化的JSON报告"""
    
    @staticmethod
    def generate(jd_parsed: Dict, resume_parsed: Dict, 
                 match_result: Dict, optimization: Dict) -> Dict:
        """生成完整的分析报告"""
        report = {
            "report_version": "1.0.0",
            "agent": "AI简历优化Agent",
            "summary": {
                "job_title": jd_parsed["title"],
                "candidate_name": resume_parsed["name"],
                "match_score": match_result["total_score"],
                "match_level": match_result["score_level"],
                "optimization_count": len(optimization["suggestions"]),
            },
            "jd_analysis": {
                "position": jd_parsed["title"],
                "required_skills": jd_parsed["required_skills"],
                "experience_required": f"{jd_parsed['experience_years']}年" if jd_parsed['experience_years'] > 0 else "未明确要求",
                "education_required": jd_parsed["education_required"] or "未明确要求",
            },
            "resume_analysis": {
                "name": resume_parsed["name"],
                "skills_found": resume_parsed["skills"],
                "education": resume_parsed["education"],
                "experience_years": resume_parsed["experience_years"],
                "project_count": resume_parsed["project_count"],
            },
            "match_analysis": match_result,
            "optimization": {
                "suggestions": optimization["suggestions"],
                "highlights": optimization["highlights"],
                "optimized_resume": optimization["optimized_resume"],
            },
        }
        return report


# ==============================================================================
# 主流程控制器
# ==============================================================================

class ResumeAgent:
    """AI简历优化Agent主控制器"""
    
    def __init__(self):
        self.jd_parser = JDParser()
        self.resume_parser = ResumeParser()
        self.match_engine = MatchEngine()
        self.optimizer = ResumeOptimizer()
        self.reporter = ReportGenerator()
    
    def run(self, jd_text: str, resume_text: str) -> Dict:
        """执行完整的简历优化流程"""
        
        print("=" * 60)
        print("  🤖 AI简历优化Agent v1.0")
        print("=" * 60)
        print()
        
        # 步骤1: JD解析
        print("📋 [步骤1/5] 解析职位描述 (JD)...")
        jd_parsed = self.jd_parser.parse(jd_text)
        print(f"   ✅ 识别职位: {jd_parsed['title']}")
        print(f"   ✅ 提取技能要求: {len(jd_parsed['required_skills'])}项")
        print(f"   ✅ 经验要求: {jd_parsed['experience_years']}年")
        print(f"   ✅ 学历要求: {jd_parsed['education_required'] or '未明确'}")
        print(f"   技能列表: {', '.join(jd_parsed['required_skills'][:8])}{'...' if len(jd_parsed['required_skills']) > 8 else ''}")
        print()
        
        # 步骤2: 简历解析
        print("📄 [步骤2/5] 解析简历...")
        resume_parsed = self.resume_parser.parse(resume_text)
        print(f"   ✅ 候选人: {resume_parsed['name']}")
        print(f"   ✅ 识别技能: {len(resume_parsed['skills'])}项")
        print(f"   ✅ 估算经验: {resume_parsed['experience_years']}年")
        print(f"   ✅ 学历: {resume_parsed['education'].get('degree', '未知')} - {resume_parsed['education'].get('school', '未知')}")
        print(f"   技能列表: {', '.join(resume_parsed['skills'][:8])}{'...' if len(resume_parsed['skills']) > 8 else ''}")
        print()
        
        # 步骤3: 匹配度计算
        print("📊 [步骤3/5] 计算匹配度...")
        match_result = self.match_engine.calculate(jd_parsed, resume_parsed)
        print(f"   🎯 综合评分: {match_result['total_score']}/100")
        print(f"   📈 匹配等级: {match_result['score_level']}")
        print(f"   分项得分:")
        for key, val in match_result["breakdown"].items():
            score = val["score"]
            max_score = val["max"]
            bar = "█" * int(score / max_score * 20) + "░" * (20 - int(score / max_score * 20))
            label = {
                "skill_coverage": "技能覆盖",
                "experience_match": "经验匹配",
                "education_match": "学历匹配",
                "project_richness": "项目丰富度",
                "skill_relevance": "技能相关度",
            }.get(key, key)
            print(f"     {label: <6}: {bar} {score}/{max_score}")
        print(f"   匹配技能: {', '.join(match_result['matched_skills'][:6])}")
        print(f"   缺失技能: {', '.join(match_result['missing_skills'][:6])}")
        print()
        
        # 步骤4: 简历优化
        print("✨ [步骤4/5] 生成优化建议...")
        optimization = self.optimizer.optimize(jd_parsed, resume_parsed, match_result)
        print(f"   ✅ 生成{len(optimization['suggestions'])}条优化建议")
        for i, sug in enumerate(optimization["suggestions"], 1):
            print(f"   [{sug['priority']}优先级] {sug['category']}: {sug['issue'][:40]}...")
        print()
        
        # 步骤5: 输出报告
        print("📝 [步骤5/5] 生成分析报告...")
        report = self.reporter.generate(jd_parsed, resume_parsed, match_result, optimization)
        print(f"   ✅ 报告生成完成")
        print()
        
        # 打印优化后的简历
        print("=" * 60)
        print("  📋 优化后简历建议")
        print("=" * 60)
        print(optimization["optimized_resume"])
        print()
        
        # 打印关键摘要
        print("=" * 60)
        print("  💡 关键优化摘要")
        print("=" * 60)
        for h in optimization["highlights"]:
            print(f"  • {h}")
        print()
        
        return report


# ==============================================================================
# 入口函数
# ==============================================================================

def main():
    """主函数：演示完整流程"""
    
    agent = ResumeAgent()
    
    print("🔧 使用预设数据运行演示...")
    print()
    
    # 使用预设数据运行
    report1 = agent.run(PRESET_JD_1, PRESET_RESUME_1)
    
    # 输出JSON报告
    print("=" * 60)
    print("  📊 JSON格式完整报告")
    print("=" * 60)
    print(json.dumps(report1, ensure_ascii=False, indent=2))
    print()
    print()
    
    # 第二组预设数据演示
    print("=" * 60)
    print("  🔄 切换到第二组预设数据")
    print("=" * 60)
    print()
    
    report2 = agent.run(PRESET_JD_2, PRESET_RESUME_2)
    
    print("=" * 60)
    print("  📊 第二组JSON格式完整报告")
    print("=" * 60)
    print(json.dumps(report2, ensure_ascii=False, indent=2))
    print()
    
    print("=" * 60)
    print("  ✅ AI简历优化Agent运行完成")
    print("  📌 共处理2组数据，所有步骤正常执行")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
