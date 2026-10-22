"""Generate the simulated teaching dataset and SPSS-style outputs for demo D10.

Every number produced here is SIMULATED for teaching (running case: anxiety
during the two-week wait after embryo transfer). "D10" is the demo's number
in the course.
Nothing describes real patients. Re-run with ``python3 make_simulated_data.py``;
the fixed seed makes all outputs reproducible.
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.formula.api as smf  # noqa: E402
from scipy import stats  # noqa: E402
from statsmodels.stats.anova import anova_lm  # noqa: E402

logger = logging.getLogger(__name__)

OUT_DIR = Path(__file__).resolve().parent
SEED = 20261104
GROUPS = ("干预组", "对照组")
TIMES = ("t0", "t1", "t2")
TIME_NAMES = ("移植日", "移植后第7天", "验孕前")
FEMALE_COLS = [f"sas_f_{t}" for t in TIMES]
MALE_COLS = [f"sas_m_{t}" for t in TIMES]
# CJK fonts tried in order (macOS, Windows, Linux)
FONTS = ["Hiragino Sans GB", "PingFang SC", "Microsoft YaHei", "SimHei", "Noto Sans CJK SC"]
SIM_NOTE = "模拟数据，仅供教学，不代表真实患者"

VARIABLE_LABELS = {
    "couple_id": "夫妻编号",
    "group": "组别",
    "f_age": "女方年龄（岁）",
    "m_age": "男方年龄（岁）",
    "infertility_years": "不孕年限（年）",
    "infertility_type": "不孕类型",
    "f_education": "女方文化程度",
    "transfer_type": "移植类型",
    "embryos_transferred": "移植胚胎数（枚）",
    "sas_f_t0": "女方 SAS 标准分·移植日",
    "sas_f_t1": "女方 SAS 标准分·移植后第7天",
    "sas_f_t2": "女方 SAS 标准分·验孕前",
    "sas_m_t0": "男方 SAS 标准分·移植日",
    "sas_m_t1": "男方 SAS 标准分·移植后第7天",
    "sas_m_t2": "男方 SAS 标准分·验孕前",
}


@dataclass(frozen=True)
class SimConfig:
    """Parameters of the simulated two-arm trial (all values are invented)."""

    n_per_group: int = 40
    female_means: tuple[tuple[float, ...], ...] = ((52.0, 51.0, 49.0), (52.0, 54.0, 56.0))
    male_means: tuple[tuple[float, ...], ...] = ((45.0, 45.5, 45.5), (45.0, 46.5, 48.5))
    female_sd: float = 8.5
    male_sd: float = 7.0
    time_corr: tuple[tuple[float, ...], ...] = (
        (1.00, 0.70, 0.50),
        (0.70, 1.00, 0.75),
        (0.50, 0.75, 1.00),
    )
    spouse_corr: float = 0.35
    t2_dropouts: tuple[int, int] = (2, 3)


@dataclass(frozen=True)
class Type3:
    """Type III sums of squares for a one-way between-subjects model."""

    intercept: float
    group: float
    error: float
    resid: np.ndarray


@dataclass(frozen=True)
class RMResult:
    """Mixed (between x within) repeated-measures ANOVA, SPSS GLM conventions."""

    n_by_group: dict[str, int]
    mauchly: dict[str, float]
    within: pd.DataFrame
    between: pd.DataFrame
    desc: pd.DataFrame
    emm: pd.DataFrame
    pairwise: pd.DataFrame


def simulate(cfg: SimConfig, rng: np.random.Generator) -> pd.DataFrame:
    """Simulate one row per couple: baseline characteristics plus SAS scores."""
    corr = np.array(cfg.time_corr)
    spouse = np.array([[1.0, cfg.spouse_corr], [cfg.spouse_corr, 1.0]])
    sds = np.array([cfg.female_sd] * 3 + [cfg.male_sd] * 3)
    cov = np.kron(spouse, corr) * np.outer(sds, sds)
    frames = []
    for g_idx, group in enumerate(GROUPS):
        mean = np.array(cfg.female_means[g_idx] + cfg.male_means[g_idx])
        scores = rng.multivariate_normal(mean, cov, size=cfg.n_per_group)
        frame = pd.DataFrame(np.clip(np.rint(scores), 25, 100), columns=FEMALE_COLS + MALE_COLS)
        frame.insert(0, "group", group)
        frames.append(frame)
    df = pd.concat(frames, ignore_index=True)
    n = len(df)
    df.insert(0, "couple_id", [f"C{i + 1:03d}" for i in range(n)])
    f_age = np.clip(np.rint(rng.normal(32, 4, n)), 22, 42)
    df.insert(2, "f_age", f_age.astype(int))
    df.insert(3, "m_age", np.clip(np.rint(f_age + rng.normal(2, 3, n)), 22, 50).astype(int))
    years = np.clip(np.rint(rng.lognormal(np.log(3), 0.55, n)), 1, 15)
    df.insert(4, "infertility_years", years.astype(int))
    df.insert(5, "infertility_type", rng.choice(["原发", "继发"], n, p=[0.6, 0.4]))
    df.insert(6, "f_education", rng.choice(["高中及以下", "大专", "本科及以上"], n, p=[0.25, 0.35, 0.40]))
    df.insert(7, "transfer_type", rng.choice(["新鲜胚胎", "冻融胚胎"], n, p=[0.45, 0.55]))
    df.insert(8, "embryos_transferred", rng.choice([1, 2], n, p=[0.7, 0.3]))
    for g_idx, group in enumerate(GROUPS):
        idx = df.index[df["group"] == group].to_numpy()
        drop = rng.choice(idx, size=cfg.t2_dropouts[g_idx], replace=False)
        df.loc[drop, ["sas_f_t2", "sas_m_t2"]] = np.nan
    df[FEMALE_COLS + MALE_COLS] = df[FEMALE_COLS + MALE_COLS].astype("Int64")
    return df


def orthonormal_contrasts(k: int) -> np.ndarray:
    """Return a k x (k-1) orthonormal basis orthogonal to the constant vector."""
    q, _ = np.linalg.qr(np.vander(np.arange(k, dtype=float), k, increasing=True))
    return q[:, 1:]


def type3(y: np.ndarray, group: np.ndarray) -> Type3:
    """Fit y ~ group with sum-to-zero contrasts and return Type III SS."""
    frame = pd.DataFrame({"y": y, "group": group})
    fit = smf.ols("y ~ C(group, Sum)", data=frame).fit()
    table = anova_lm(fit, typ=3)
    ss = dict(zip(table.index, table["sum_sq"].to_numpy(dtype=float)))
    return Type3(
        intercept=float(ss["Intercept"]),
        group=float(ss["C(group, Sum)"]),
        error=float(ss["Residual"]),
        resid=fit.resid.to_numpy(),
    )


def rm_anova(complete: pd.DataFrame) -> RMResult:
    """Run the univariate mixed RM-ANOVA exactly as SPSS GLM computes it."""
    y = complete[FEMALE_COLS].to_numpy(dtype=float)
    group = complete["group"].to_numpy()
    n_total, k = y.shape
    g, p = len(GROUPS), k - 1
    df_b = n_total - g
    z = y @ orthonormal_contrasts(k)
    fits = [type3(z[:, j], group) for j in range(p)]
    ss_time = sum(f.intercept for f in fits)
    ss_tg = sum(f.group for f in fits)
    ss_err = sum(f.error for f in fits)
    resid = np.column_stack([f.resid for f in fits])
    s_mat = resid.T @ resid / df_b
    w = np.linalg.det(s_mat) / (np.trace(s_mat) / p) ** p
    chi2 = -(df_b - (2 * p**2 + p + 2) / (6 * p)) * np.log(w)
    chi2_df = p * (p + 1) // 2 - 1
    eps_gg = np.trace(s_mat) ** 2 / (p * np.trace(s_mat @ s_mat))
    eps_hf = min(1.0, (n_total * p * eps_gg - 2) / (p * (df_b - p * eps_gg)))
    corrections = (("假设球形度", 1.0), ("格林豪斯-盖斯勒", eps_gg), ("辛-费德特", eps_hf), ("下限", 1 / p))
    df_err = p * df_b
    rows = []
    for effect, ss, df_eff in (("时间", ss_time, p), ("时间 * 组别", ss_tg, p * (g - 1))):
        f_val = (ss / df_eff) / (ss_err / df_err)
        for label, eps in corrections:
            d1, d2 = df_eff * eps, df_err * eps
            rows.append([effect, label, ss, d1, ss / d1, f_val, stats.f.sf(f_val, d1, d2), ss / (ss + ss_err)])
    for label, eps in corrections:
        rows.append(["误差（时间）", label, ss_err, df_err * eps, ss_err / (df_err * eps), np.nan, np.nan, np.nan])
    within = pd.DataFrame(rows, columns=["源", "校正", "III类平方和", "自由度", "均方", "F", "显著性", "偏Eta平方"])

    avg = type3(y @ (np.ones(k) / np.sqrt(k)), group)
    mse_b = avg.error / df_b
    between_rows = []
    for name, ss, df_eff in (("截距", avg.intercept, 1), ("组别", avg.group, g - 1)):
        f_val = (ss / df_eff) / mse_b
        between_rows.append([name, ss, df_eff, ss / df_eff, f_val, stats.f.sf(f_val, df_eff, df_b), ss / (ss + avg.error)])
    between_rows.append(["误差", avg.error, df_b, mse_b, np.nan, np.nan, np.nan])
    between = pd.DataFrame(between_rows, columns=["源", "III类平方和", "自由度", "均方", "F", "显著性", "偏Eta平方"])

    tcrit = stats.t.ppf(0.975, df_b)
    n_by_group = {gr: int((group == gr).sum()) for gr in GROUPS}
    desc_rows, emm_rows, pair_rows = [], [], []
    for t_idx, t_name in enumerate(TIME_NAMES):
        col = y[:, t_idx]
        mse = type3(col, group).error / df_b
        means = {gr: col[group == gr].mean() for gr in GROUPS}
        for gr in GROUPS:
            vals = col[group == gr]
            desc_rows.append([t_name, gr, vals.mean(), vals.std(ddof=1), len(vals)])
            se = np.sqrt(mse / n_by_group[gr])
            emm_rows.append([gr, t_name, means[gr], se, means[gr] - tcrit * se, means[gr] + tcrit * se])
        desc_rows.append([t_name, "总计", col.mean(), col.std(ddof=1), len(col)])
        for a, b in ((GROUPS[0], GROUPS[1]), (GROUPS[1], GROUPS[0])):
            diff = means[a] - means[b]
            se = np.sqrt(mse * (1 / n_by_group[a] + 1 / n_by_group[b]))
            p_val = min(1.0, 2 * stats.t.sf(abs(diff / se), df_b))
            pair_rows.append([t_name, a, b, diff, se, p_val, diff - tcrit * se, diff + tcrit * se])
    return RMResult(
        n_by_group=n_by_group,
        mauchly={"W": float(w), "chi2": float(chi2), "df": float(chi2_df),
                 "p": float(stats.chi2.sf(chi2, chi2_df)), "gg": float(eps_gg), "hf": float(eps_hf),
                 "lb": 1 / p},
        within=within,
        between=between,
        desc=pd.DataFrame(desc_rows, columns=["时间", "组别", "平均值", "标准偏差", "个案数"]),
        emm=pd.DataFrame(emm_rows, columns=["组别", "时间", "平均值", "标准误差", "95%CI下限", "95%CI上限"]),
        pairwise=pd.DataFrame(pair_rows, columns=["时间", "(I)组别", "(J)组别", "平均值差值(I-J)", "标准误差",
                                                  "显著性", "差值95%CI下限", "差值95%CI上限"]),
    )


def mixed_model_sensitivity(df: pd.DataFrame) -> dict[str, float]:
    """Likelihood-ratio test of group x time using all available female data."""
    long = df.melt(id_vars=["couple_id", "group"], value_vars=FEMALE_COLS, var_name="time", value_name="sas")
    long = long.dropna().astype({"sas": float})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        full = smf.mixedlm("sas ~ C(group) * C(time)", long, groups=long["couple_id"]).fit(reml=False)
        reduced = smf.mixedlm("sas ~ C(group) + C(time)", long, groups=long["couple_id"]).fit(reml=False)
    lr = 2 * (full.llf - reduced.llf)
    return {"lr": float(lr), "df": 2.0, "p": float(stats.chi2.sf(lr, 2)),
            "n_obs": float(len(long)), "n_women": float(long["couple_id"].nunique())}


def f3(x: float) -> str:
    """Format like SPSS: three decimals, no leading zero for |x| < 1."""
    if pd.isna(x):
        return ""
    s = f"{x:.3f}"
    return s.replace("0.", ".", 1) if s.startswith(("0.", "-0.")) else s


def fp(p: float) -> str:
    """Format a significance value like SPSS (shows .000 below .0005)."""
    return "" if pd.isna(p) else (".000" if p < 0.0005 else f3(p))


def fdf(x: float) -> str:
    """Format degrees of freedom: integers plain, corrected df with three decimals."""
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f3(x)


def spss_tables(res: RMResult) -> list[tuple[str, pd.DataFrame, str]]:
    """Build display tables (strings) in SPSS Chinese-output style."""
    m = res.mauchly
    mauchly = pd.DataFrame([["时间", f3(m["W"]), f3(m["chi2"]), fdf(m["df"]), fp(m["p"]),
                             f3(m["gg"]), f3(m["hf"]), f3(m["lb"])]],
                           columns=["主体内效应", "莫奇来 W", "近似卡方", "自由度", "显著性",
                                    "ε 格林豪斯-盖斯勒", "ε 辛-费德特", "ε 下限"])
    within = res.within.copy()
    within["源"] = within["源"].where(within["源"] != within["源"].shift(), "")
    within = within.assign(**{"III类平方和": within["III类平方和"].map(f3), "自由度": within["自由度"].map(fdf),
                              "均方": within["均方"].map(f3), "F": within["F"].map(f3),
                              "显著性": within["显著性"].map(fp), "偏Eta平方": within["偏Eta平方"].map(f3)})
    between = res.between.assign(**{"III类平方和": res.between["III类平方和"].map(f3),
                                    "自由度": res.between["自由度"].map(fdf), "均方": res.between["均方"].map(f3),
                                    "F": res.between["F"].map(f3), "显著性": res.between["显著性"].map(fp),
                                    "偏Eta平方": res.between["偏Eta平方"].map(f3)})
    desc = res.desc.assign(平均值=res.desc["平均值"].map(f3), 标准偏差=res.desc["标准偏差"].map(f3),
                           个案数=res.desc["个案数"].astype(str))
    emm = res.emm.assign(**{c: res.emm[c].map(f3) for c in ["平均值", "标准误差", "95%CI下限", "95%CI上限"]})
    pair = res.pairwise.assign(**{c: res.pairwise[c].map(f3) for c in
                                  ["平均值差值(I-J)", "标准误差", "差值95%CI下限", "差值95%CI上限"]})
    pair["显著性"] = res.pairwise["显著性"].map(fp)
    note_design = "a. 设计：截距 + 组别；主体内设计：时间。"
    return [
        ("描述统计（女方 SAS 标准分）", desc, ""),
        ("Mauchly 球形度检验（见注 a）", mauchly, note_design + "检验正交化转换后因变量的误差协方差矩阵与单位矩阵成比例的原假设。"),
        ("主体内效应检验", within, "测量：女方 SAS 标准分"),
        ("主体间效应检验", between, "测量：女方 SAS 标准分；转换的变量：平均值"),
        ("估算边际平均值：组别 * 时间", emm, ""),
        ("成对比较（各时间点组间比较）", pair, "基于估算边际平均值。多重比较调节：邦弗伦尼。"),
    ]


def md_table(df: pd.DataFrame) -> str:
    """Render a DataFrame of strings as a GitHub-flavoured Markdown table."""
    head = "| " + " | ".join(df.columns) + " |"
    sep = "|" + "|".join(["---"] * len(df.columns)) + "|"
    body = ["| " + " | ".join(str(v) for v in row) + " |" for row in df.to_numpy()]
    return "\n".join([head, sep, *body])


def render_png(blocks: list[tuple[str, pd.DataFrame, str]], path: Path) -> None:
    """Render tables as an SPSS-like screenshot (white, thin grey grid)."""
    plt.rcParams["font.family"] = FONTS
    heights = [1.1 + 0.36 * (len(df) + 1) for _, df, _ in blocks]
    fig, axes = plt.subplots(len(blocks), 1, figsize=(12, sum(heights)),
                             gridspec_kw={"height_ratios": heights})
    for ax, (title, df, note) in zip(np.atleast_1d(axes), blocks):
        ax.axis("off")
        ax.set_title(title, fontsize=12, fontweight="bold")
        tbl = ax.table(cellText=df.to_numpy().tolist(), colLabels=list(df.columns),
                       cellLoc="center", bbox=[0, 0.16, 1, 0.84])
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(9)
        for (row, _), cell in tbl.get_celld().items():
            cell.set_edgecolor("#c9c9c9")
            cell.set_linewidth(0.6)
            if row == 0:
                cell.set_facecolor("#eef1f5")
                cell.set_text_props(fontweight="bold")
        if note:
            ax.text(0, 0.04, note, transform=ax.transAxes, fontsize=8, color="#444444")
    fig.text(0.99, 0.002, SIM_NOTE, ha="right", fontsize=8, color="#b00020")
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def baseline_table(df: pd.DataFrame) -> pd.DataFrame:
    """Table 1 by randomised group, CONSORT style (no P-value column)."""
    cols = [f"{gr}（n={int((df['group'] == gr).sum())}）" for gr in GROUPS]
    rows: list[list[str]] = []

    def per_group(fn) -> list[str]:  # noqa: ANN001
        return [fn(df.loc[df["group"] == gr]) for gr in GROUPS]

    for label, col in (("女方年龄（岁），x̄±s", "f_age"), ("男方年龄（岁），x̄±s", "m_age")):
        rows.append([label, *per_group(lambda d, c=col: f"{d[c].mean():.1f}±{d[c].std(ddof=1):.1f}")])
    rows.append(["不孕年限（年），M(P25, P75)", *per_group(
        lambda d: f"{d['infertility_years'].median():.0f}({d['infertility_years'].quantile(.25):.0f}, "
                  f"{d['infertility_years'].quantile(.75):.0f})")])
    for label, col, levels in (("不孕类型，n(%)", "infertility_type", ["原发", "继发"]),
                               ("女方文化程度，n(%)", "f_education", ["高中及以下", "大专", "本科及以上"]),
                               ("移植类型，n(%)", "transfer_type", ["新鲜胚胎", "冻融胚胎"]),
                               ("移植胚胎数，n(%)", "embryos_transferred", [1, 2])):
        rows.append([label, "", ""])
        for lv in levels:
            rows.append([f"　{lv}{'枚' if col == 'embryos_transferred' else ''}", *per_group(
                lambda d, c=col, v=lv: f"{(d[c] == v).sum()}({(d[c] == v).mean() * 100:.1f})")])
    rows.append(["女方 SAS 标准分·移植日，x̄±s", *per_group(
        lambda d: f"{d['sas_f_t0'].astype(float).mean():.1f}±{d['sas_f_t0'].astype(float).std(ddof=1):.1f}")])
    return pd.DataFrame(rows, columns=["项目", *cols])


def answer_key(res: RMResult, sens: dict[str, float], n_random: int) -> str:
    """Write the answer key: what a correct interpretation must contain."""
    m = res.mauchly
    use_gg = m["p"] < 0.05
    corr = "格林豪斯-盖斯勒" if use_gg else "假设球形度"
    w = res.within[res.within["校正"] == corr].set_index("源")
    inter, time_eff = w.loc["时间 * 组别"], w.loc["时间"]
    grp = res.between.set_index("源").loc["组别"]
    pw = res.pairwise[res.pairwise["(I)组别"] == GROUPS[0]].set_index("时间")
    t2 = pw.loc[TIME_NAMES[2]]
    n_c = sum(res.n_by_group.values())

    def pstr(p: float) -> str:
        return "P<0.001" if p < 0.001 else f"P={p:.3f}"

    lines = [
        "# D10 参考答案要点（模拟数据，仅供教学）", "",
        "用来核对 AI 的解读对不对。数字由 make_simulated_data.py 计算，并经 verify_with_r.R 用 R car 包独立复算。", "",
        "## 1. 先复述（AI 应先读对这些数字）",
        f"- 随机分组 {n_random} 对夫妻；女方三次测量完整者 {n_c} 例（干预组 {res.n_by_group[GROUPS[0]]}，"
        f"对照组 {res.n_by_group[GROUPS[1]]}），{n_random - n_c} 例验孕前问卷缺失，按完全病例分析",
        f"- Mauchly 检验：W={m['W']:.3f}，χ²={m['chi2']:.3f}，自由度 {m['df']:.0f}，{pstr(m['p'])}"
        + ("→ 不满足球形假设，应报告格林豪斯-盖斯勒校正结果" if use_gg else "→ 满足球形假设"), "",
        "## 2. 正确解读的要点",
        f"- **组别 × 时间交互作用**：F({inter['自由度']:.2f}, {w.loc['误差（时间）', '自由度']:.2f})={inter['F']:.2f}，"
        f"{pstr(inter['显著性'])}，偏 η²={inter['偏Eta平方']:.3f}——两组焦虑随时间的变化趋势不同，这是本研究的核心结果",
        f"- 时间主效应：F={time_eff['F']:.2f}，{pstr(time_eff['显著性'])}",
        f"- 组别主效应：F(1, {int(res.between.set_index('源').loc['误差', '自由度'])})={grp['F']:.2f}，{pstr(grp['显著性'])}"
        "。组别主效应是三个时点（含基线）平均后的比较，交互作用显著时应以简单效应解释，不能据组别主效应判断干预是否有效",
        "- 各时点组间比较（干预组−对照组）：",
    ]
    for t_name in TIME_NAMES:
        r = pw.loc[t_name]
        lines.append(f"  - {t_name}：均数差 {r['平均值差值(I-J)']:.2f}（95%CI：{r['差值95%CI下限']:.2f} 至 "
                     f"{r['差值95%CI上限']:.2f}），{pstr(r['显著性'])}")
    lines += [
        "",
        "## 3. 规范结果句（参考）",
        f"- 中文：重复测量方差分析显示，组别与时间的交互作用有统计学意义（经格林豪斯-盖斯勒校正，"
        f"F={inter['F']:.2f}，{pstr(inter['显著性'])}，偏η²={inter['偏Eta平方']:.3f}）。验孕前干预组女性 SAS 标准分低于对照组"
        f"（均数差{t2['平均值差值(I-J)']:.2f}，95%CI：{t2['差值95%CI下限']:.2f}至{t2['差值95%CI上限']:.2f}，{pstr(t2['显著性'])}）。"
        if use_gg else "- 中文：（球形假设成立，按假设球形度结果书写）",
        "",
        "## 4. AI 容易出错的地方",
        "- SPSS 显示的「.000」要写成 P<0.001，不能写 P=0.000",
        "- 组别主效应与交互作用的含义不能混淆",
        "- 完全病例分析丢掉了缺失者；敏感性分析可用线性混合模型纳入全部可用数据：",
        f"  - 随机截距混合模型（{sens['n_women']:.0f} 名女性、{sens['n_obs']:.0f} 个观测），交互项似然比检验 "
        f"χ²({sens['df']:.0f})={sens['lr']:.2f}，{pstr(sens['p'])}",
        "- 差值是否有临床意义，需要对照最小临床意义差值（SAS 尚无公认值，需查文献）",
        "- 只能说「降低等待期焦虑」，不能外推到妊娠率（治疗前焦虑与妊娠结局无关，见 Boivin 等, BMJ, 2011）",
        "- 丈夫数据（sas_m_*）与妻子数据不独立，不能和女方合并成一个样本分析",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Generate data, run the analysis, and write every teaching artefact."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    rng = np.random.default_rng(SEED)
    df = simulate(SimConfig(), rng)
    df.to_csv(OUT_DIR / "等待期焦虑_模拟数据.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(OUT_DIR / "等待期焦虑_模拟数据.xlsx") as writer:
        df.to_excel(writer, sheet_name="数据", index=False)
        labels = pd.DataFrame({"变量名": list(VARIABLE_LABELS), "含义": list(VARIABLE_LABELS.values())})
        labels.loc[len(labels)] = ["说明", SIM_NOTE]
        labels.to_excel(writer, sheet_name="变量说明", index=False)

    complete = df.dropna(subset=FEMALE_COLS).reset_index(drop=True)
    res = rm_anova(complete)
    sens = mixed_model_sensitivity(df)
    blocks = spss_tables(res)

    md = [f"# D10 SPSS 风格输出：女方 SAS 标准分重复测量方差分析\n\n> {SIM_NOTE}。练习时把下面的表格粘贴给 Kimi（05 卡）。\n"]
    md += [f"## {title}\n\n{md_table(table)}\n" + (f"\n{note}\n" if note else "") for title, table, note in blocks]
    (OUT_DIR / "D10_SPSS风格输出.md").write_text("\n".join(md), encoding="utf-8")
    render_png(blocks[:4], OUT_DIR / "D10_SPSS风格输出_1.png")
    render_png(blocks[4:], OUT_DIR / "D10_SPSS风格输出_2.png")

    t1 = baseline_table(df)
    (OUT_DIR / "基线表_Table1.md").write_text(
        f"# 表 1　两组研究对象基线资料比较\n\n> {SIM_NOTE}\n\n{md_table(t1)}\n\n"
        "注：随机对照试验按 CONSORT 不对基线做显著性检验；不孕年限呈偏态分布，以 M(P25, P75) 表示。\n",
        encoding="utf-8")
    (OUT_DIR / "D10_答案要点.md").write_text(answer_key(res, sens, len(df)), encoding="utf-8")
    logger.info("Mauchly W=%.3f p=%.4f GG=%.3f", res.mauchly["W"], res.mauchly["p"], res.mauchly["gg"])
    logger.info("Within:\n%s", res.within.round(4).to_string())
    logger.info("Between:\n%s", res.between.round(4).to_string())
    logger.info("Pairwise:\n%s", res.pairwise.round(4).to_string())
    logger.info("Sensitivity: %s", {k: round(v, 4) for k, v in sens.items()})


if __name__ == "__main__":
    main()
