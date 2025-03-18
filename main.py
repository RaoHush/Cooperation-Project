import sys
import random
import fractions
import argparse
import re

def generate_number(r, non_zero=False):
    """安全生成数值"""
    if random.choice([True, False]):
        return random.randint(1 if non_zero else 0, r - 1)
    else:
        numerator = random.randint(1, r - 1)
        denominator = random.randint(max(numerator + 1, 2), r)
        if non_zero:
            while denominator == 0:
                denominator = random.randint(max(numerator + 1, 2), r)
        return fractions.Fraction(numerator, denominator)


def generate_expression(r, ops_remaining=1):
    """核心生成函数：支持1-3个运算符，规范化表达式结构"""
    if ops_remaining == 0:
        num = generate_number(r)
        return format_fraction(num), num

    left_ops = random.randint(0, ops_remaining - 1)
    right_ops = ops_remaining - 1 - left_ops
    operator = random.choice(['+', '-', '×', '÷'])

    # 递归生成子树
    e1_str, e1_val = (generate_expression(r, left_ops) if left_ops > 0 else
                      (format_fraction(generate_number(r)), generate_number(r)))
    e2_str, e2_val = (generate_expression(r, right_ops) if right_ops > 0 else
                      (format_fraction(generate_number(r)), generate_number(r)))

    # 处理运算符约束
    if operator == '-':
        if e1_val < e2_val:
            e1_str, e2_str = e2_str, e1_str
            e1_val, e2_val = e2_val, e1_val
    elif operator == '÷':
        e2_str, e2_val = (format_fraction(generate_number(r, True)), generate_number(r, True))
        while e2_val == 0:
            e2_str, e2_val = (format_fraction(generate_number(r, True)), generate_number(r, True))

    # 交换律规范化：确保加法/乘法的操作数按字典序排列
    if operator in ['+', '×']:
        if e1_str > e2_str:  # 字典序比较
            e1_str, e2_str = e2_str, e1_str
            e1_val, e2_val = e2_val, e1_val

    # 智能括号优化
    op_priority = {'+': 1, '-': 1, '×': 2, '÷': 2}
    e1_needs_parens = any(op in e1_str for op in ['+', '-']) and op_priority[operator] > 1
    e2_needs_parens = any(op in e2_str for op in ['+', '-']) and op_priority[operator] > 1

    if e1_needs_parens:
        e1_str = f"({e1_str})"
    if e2_needs_parens:
        e2_str = f"({e2_str})"

    expr_str = f"{e1_str} {operator} {e2_str}"
    return expr_str, calculate_expression(expr_str)


def format_fraction(f):
    """分数格式化（与原代码一致）"""
    if isinstance(f, fractions.Fraction):
        if f.denominator == 1:
            return str(f.numerator)
        whole = f.numerator // f.denominator
        remainder = f.numerator % f.denominator
        if whole > 0:
            return f"{whole}'{remainder}/{f.denominator}" if remainder else f"{whole}"
        return f"{f.numerator}/{f.denominator}"
    return str(f)


def calculate_expression(expr):
    """表达式计算（与原代码一致）"""
    try:
        expr = expr.replace('×', '*').replace('÷', '/')
        expr = re.sub(r"(\d+)'(\d+)/(\d+)", r"Fraction(\1*\3+\2,\3)", expr)
        expr = re.sub(r"(\d+)/(\d+)", r"Fraction(\1,\2)", expr)
        expr = re.sub(r"\b(\d+)\b", r"Fraction(\1,1)", expr)

        for match in re.finditer(r"Fraction\(\d+,\s*(-?\d+)\)", expr):
            denominator = int(match.group(1))
            if denominator == 0:
                raise ZeroDivisionError("Generated expression has division by zero.")
        return eval(expr, {'__builtins__': None}, {'Fraction': fractions.Fraction})
    except ZeroDivisionError:
        raise
    except Exception as e:
        raise ValueError(f"Error calculating expression: {e}")


def generate_problems(n, r):
    """题目生成入口（添加去重机制）"""
    exercises = []
    answers = []
    seen_expressions = set()  # 用于记录已生成的表达式

    for problem_num in range(1, n + 1):
        for _ in range(100):
            ops_count = random.randint(1, 3)
            expr_str, answer = generate_expression(r, ops_count)

            # 检查表达式是否重复
            if expr_str in seen_expressions:
                continue
            seen_expressions.add(expr_str)

            if answer.denominator != 0 and answer >= 0:
                actual_ops = sum(expr_str.count(op) for op in ['+', '-', '×', '÷'])
                if actual_ops == ops_count:
                    verified_answer = format_fraction(calculate_expression(expr_str))
                    if format_fraction(answer) == verified_answer:
                        exercises.append(f"{problem_num}. {expr_str} = ")
                        answers.append(f"{problem_num}. {verified_answer}")
                        break
        else:
            raise ValueError(f"生成失败，请增大-r值(当前r={r})")

    with open("Exercises.txt", "w") as f:
        f.write("\n".join(exercises))
    with open("Answers.txt", "w") as f:
        f.write("\n".join(answers))


# grade_answers 和 main 函数保持不变（省略以节省空间）
def grade_answers(exercise_file, answer_file):
    """答案校对"""
    with open(exercise_file) as f:
        exercises = f.readlines()
    with open(answer_file) as f:
        answers = f.readlines()

    correct, wrong = [], []

    for ex, ans in zip(exercises, answers):
        try:
            # 解析题号
            ex_num, ex_expr = ex.strip().split('.', 1)
            ans_num, ans_val = ans.strip().split('.', 1)

            if int(ex_num) != int(ans_num):
                raise ValueError("题号不匹配")

            # 计算正确答案
            expr = ex_expr.split('=', 1)[0].strip()
            correct_answer = format_fraction(calculate_expression(expr))

            # 比对答案
            if ans_val.strip() == correct_answer:
                correct.append(int(ex_num))
            else:
                wrong.append(int(ex_num))
        except Exception as e:
            wrong.append(int(ex_num))  # 如果出错，也归类为错误答案

    # 输出结果
    with open("Grade.txt", "w") as f:
        f.write(f"Correct: {len(correct)} ({', '.join(map(str, sorted(correct)))})\n")
        f.write(f"Wrong: {len(wrong)} ({', '.join(map(str, sorted(wrong)))})\n")


def main():
    parser = argparse.ArgumentParser(description="四则运算题目生成器及答案校对工具")
    parser.add_argument("-n", type=int, help="生成题目数量")
    parser.add_argument("-r", type=int, help="数值范围")
    parser.add_argument("-e", type=str, help="题目文件路径")
    parser.add_argument("-a", type=str, help="答案文件路径")

    args = parser.parse_args()

    if args.n and args.r:
        generate_problems(args.n, args.r)
    elif args.e and args.a:
        grade_answers(args.e, args.a)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()