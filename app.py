import math
from datetime import datetime

import pandas as pd  # type: ignore
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
import streamlit as st

# アプリのタイトルとスタイルの設定
st.set_page_config(page_title="俺の分配可能額", page_icon="💰", layout="wide")

# カスタムCSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2563EB;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #3B82F6;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .reference {
        font-size: 0.8rem;
        color: #6B7280;
        font-style: italic;
    }
    .result-box {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .positive {
        color: #059669;
    }
    .negative {
        color: #DC2626;
    }
    .info-box {
        background-color: #EFF6FF;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3B82F6;
        border-right: 4px solid #3B82F6;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #FEF3C7;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #F59E0B;
        border-right: 4px solid #F59E0B;
        margin: 1rem 0;
    }
    .danger-box {
        background-color: #FEF2F2;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #EF4444;
        border-right: 4px solid #EF4444;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


def format_yen(value):
    """金額を日本円表示形式でフォーマットする"""
    if value is None:
        return "0円"
    return f"{value:,}円"


def format_currency_input(value):
    """入力された金額文字列を数値に変換する"""
    if value is None or value == "":
        return 0
    try:
        # カンマを削除して数値に変換
        return int(value.replace(",", "").replace("円", ""))
    except ValueError:
        return 0


# アプリのメインタイトル
st.markdown(
    "<div class='main-header'>俺の分配可能額</div>",
    unsafe_allow_html=True,
)

# サイドバーで計算モードの選択
calculation_mode = st.sidebar.radio(
    "計算モード選択", ["基本モード（主要項目のみ）", "詳細モード（全項目）"]
)

# サイドバーの使い方ガイド
st.sidebar.markdown("---")
st.sidebar.markdown("### 使い方ガイド")
st.sidebar.markdown(
    """
1. **計算モードの選択**
   * 基本モード：主要項目のみで計算
   * 詳細モード：最終事業年度末日後の変動を考慮した詳細な計算

2. **基本情報の入力**
   * 純資産の部の情報を入力
   * のれんや繰延資産がある場合はその金額を入力

3. **分配可能額の計算**
   * すべての必要情報を入力後、「分配可能額を計算する」ボタンをクリック
   * 計算結果は「分配可能額結果」タブに表示

4. **結果の確認**
   * 分配可能額の総額と計算過程の詳細を確認
   * グラフ表示タブで視覚的な分析を確認

5. **注意事項**
   * 計算結果はあくまで参考値です。
   * 実際の配当や自己株式取得を行う際は、専門家に相談してください。
"""
)

# サイドバーの注意事項
st.sidebar.markdown("---")
st.sidebar.markdown("### 注意事項")
st.sidebar.markdown(
    """
    * 計算結果はあくまで参考値です。
    * 実際の配当や自己株式取得を行う際は、専門家に相談してください。
"""
)

# 初期値の設定（自動計算用）
if "results" not in st.session_state:
    st.session_state.results = {
        "retained_earnings": 0,
        "adjustments": {},
        "distributable_amount": 0,
    }

# タブの設定
tabs = st.tabs(["基本情報入力", "分配可能額結果", "グラフ表示"])

with tabs[0]:
    st.markdown("<div class='sub-header'>基本情報入力</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            "<div class='section-header'>純資産の部の情報（最終事業年度末日時点）</div>",
            unsafe_allow_html=True,
        )

        capital_stock = st.number_input(
            "資本金", min_value=0, value=0, step=1000000, format="%d"
        )
        capital_reserve = st.number_input(
            "資本準備金", min_value=0, value=0, step=1000000, format="%d"
        )
        other_capital_surplus = st.number_input(
            "その他資本剰余金", min_value=0, value=0, step=1000000, format="%d"
        )
        earned_reserve = st.number_input(
            "利益準備金", min_value=0, value=0, step=1000000, format="%d"
        )
        other_retained_earnings = st.number_input(
            "その他利益剰余金",
            min_value=-1000000000,
            value=0,
            step=1000000,
            format="%d",
        )

        # 自己株式
        treasury_stock = st.number_input(
            "自己株式（マイナス表記）",
            min_value=-1000000000,
            value=0,
            step=1000000,
            format="%d",
        )

    with col2:
        st.markdown(
            "<div class='section-header'>のれん・繰延資産</div>", unsafe_allow_html=True
        )

        goodwill = st.number_input(
            "のれんの額", min_value=0, value=0, step=1000000, format="%d"
        )
        deferred_assets = st.number_input(
            "繰延資産の額", min_value=0, value=0, step=1000000, format="%d"
        )

        st.markdown(
            "<div class='section-header'>評価・換算差額等</div>",
            unsafe_allow_html=True,
        )

        securities_valuation = st.number_input(
            "その他有価証券評価差額金",
            min_value=-1000000000,
            value=0,
            step=1000000,
            format="%d",
        )
        land_revaluation = st.number_input(
            "土地再評価差額金",
            min_value=-1000000000,
            value=0,
            step=1000000,
            format="%d",
        )

    if calculation_mode == "詳細モード（全項目）":
        st.markdown(
            "<div class='section-header'>最終事業年度末日後の計数変動</div>",
            unsafe_allow_html=True,
        )

        col3, col4 = st.columns(2)

        with col3:
            # 自己株式の処分・消却
            st.markdown("##### 自己株式の処分・消却")
            disposal_treasury_stock = st.number_input(
                "処分した自己株式の帳簿価額",
                min_value=0,
                value=0,
                step=1000000,
                format="%d",
            )
            disposal_consideration = st.number_input(
                "処分した自己株式の対価",
                min_value=0,
                value=0,
                step=1000000,
                format="%d",
            )
            canceled_treasury_stock = st.number_input(
                "消却した自己株式の帳簿価額",
                min_value=0,
                value=0,
                step=1000000,
                format="%d",
            )

            # 資本金・準備金の増減
            st.markdown("##### 資本金・準備金の増減")
            capital_reduction = st.number_input(
                "資本金減少額（準備金積立分を除く）",
                min_value=0,
                value=0,
                step=1000000,
                format="%d",
            )
            reserve_reduction = st.number_input(
                "準備金減少額（資本金積立分を除く）",
                min_value=0,
                value=0,
                step=1000000,
                format="%d",
            )
            surplus_to_capital = st.number_input(
                "剰余金から資本金・準備金へ振替えた額",
                min_value=0,
                value=0,
                step=1000000,
                format="%d",
            )

        with col4:
            # 剰余金の配当
            st.markdown("##### 最終事業年度末日後の剰余金の配当")
            dividend_amount = st.number_input(
                "剰余金配当額", min_value=0, value=0, step=1000000, format="%d"
            )
            dividend_reserve = st.number_input(
                "配当に伴う準備金積立額",
                min_value=0,
                value=0,
                step=1000000,
                format="%d",
            )

            # 臨時決算の情報
            st.markdown("##### 臨時決算の情報")
            interim_settlement = st.checkbox("臨時決算を実施")

            interim_profit = 0
            interim_loss = 0
            interim_treasury_disposal = 0

            if interim_settlement:
                interim_profit = st.number_input(
                    "臨時決算書類の当期純利益",
                    min_value=0,
                    value=0,
                    step=1000000,
                    format="%d",
                )
                interim_loss = st.number_input(
                    "臨時決算書類の当期純損失",
                    min_value=0,
                    value=0,
                    step=1000000,
                    format="%d",
                )
                interim_treasury_disposal = st.number_input(
                    "臨時決算期間内の自己株式処分対価",
                    min_value=0,
                    value=0,
                    step=1000000,
                    format="%d",
                )
    else:
        # 基本モードではデフォルト値をセット
        disposal_treasury_stock = 0
        disposal_consideration = 0
        canceled_treasury_stock = 0
        capital_reduction = 0
        reserve_reduction = 0
        surplus_to_capital = 0
        dividend_amount = 0
        dividend_reserve = 0
        interim_settlement = False
        interim_profit = 0
        interim_loss = 0
        interim_treasury_disposal = 0

    # 計算ボタン - より明確なフィードバックを提供
    calc_button = st.button(
        "分配可能額を計算する", type="primary", use_container_width=True
    )

    if calc_button:
        with st.spinner("分配可能額を計算中..."):
            # 剰余金の額の計算
            surplus_amount = other_capital_surplus + other_retained_earnings

            # 剰余金の額の調整
            treasury_stock_adjustments = (
                disposal_consideration
                - disposal_treasury_stock
                - canceled_treasury_stock
            )
            capital_reserve_adjustments = (
                capital_reduction + reserve_reduction - surplus_to_capital
            )
            dividend_adjustments = -(dividend_amount + dividend_reserve)

            # 自己株式についての調整
            treasury_stock_abs = abs(treasury_stock)
            additional_treasury_adjustments = -disposal_consideration

            # 臨時決算に伴う調整
            interim_settlement_adjustments = 0
            if interim_settlement:
                interim_settlement_adjustments = (
                    interim_profit - interim_loss + interim_treasury_disposal
                )

            # のれん等調整額の計算
            goodwill_adjustment = math.floor(goodwill / 2)
            deferred_asset_adjustment = deferred_assets
            goodwill_deferred_adjustment = (
                goodwill_adjustment + deferred_asset_adjustment
            )

            # 資本金と準備金の合計
            capital_reserve_total = capital_stock + capital_reserve + earned_reserve

            # のれん等調整額の分配可能額からの控除額計算
            if goodwill_deferred_adjustment <= capital_reserve_total:
                goodwill_deferred_deduction = 0
            elif (
                goodwill_deferred_adjustment
                <= capital_reserve_total + other_capital_surplus
            ):
                goodwill_deferred_deduction = (
                    goodwill_deferred_adjustment - capital_reserve_total
                )
            elif goodwill_adjustment <= capital_reserve_total + other_capital_surplus:
                goodwill_deferred_deduction = (
                    goodwill_deferred_adjustment - capital_reserve_total
                )
            else:
                goodwill_deferred_deduction = (
                    other_capital_surplus + deferred_asset_adjustment
                )

            # 評価換算差額等の調整
            valuation_adjustments = 0
            if securities_valuation < 0:
                valuation_adjustments -= abs(securities_valuation)
            if land_revaluation < 0:
                valuation_adjustments -= abs(land_revaluation)

            # 純資産額300万円維持のための調整
            min_net_assets = 3000000
            net_assets = (
                capital_stock
                + capital_reserve
                + earned_reserve
                + other_capital_surplus
                + other_retained_earnings
                + treasury_stock
            )
            net_assets_adjustment = 0

            if net_assets < min_net_assets:
                net_assets_adjustment = min_net_assets - net_assets

            # 分配可能額の計算
            distributable_amount = (
                surplus_amount
                + treasury_stock_adjustments
                + capital_reserve_adjustments
                + dividend_adjustments
                - treasury_stock_abs
                + additional_treasury_adjustments
                + interim_settlement_adjustments
                - goodwill_deferred_deduction
                + valuation_adjustments
                - net_assets_adjustment
            )

            # 結果を保存
            st.session_state.results = {
                "surplus_amount": surplus_amount,
                "treasury_stock_adjustments": treasury_stock_adjustments,
                "capital_reserve_adjustments": capital_reserve_adjustments,
                "dividend_adjustments": dividend_adjustments,
                "treasury_stock_abs": treasury_stock_abs,
                "additional_treasury_adjustments": additional_treasury_adjustments,
                "interim_settlement_adjustments": interim_settlement_adjustments,
                "goodwill_deferred_deduction": goodwill_deferred_deduction,
                "valuation_adjustments": valuation_adjustments,
                "net_assets_adjustment": net_assets_adjustment,
                "distributable_amount": distributable_amount,
                "capital_stock": capital_stock,
                "capital_reserve": capital_reserve,
                "other_capital_surplus": other_capital_surplus,
                "earned_reserve": earned_reserve,
                "other_retained_earnings": other_retained_earnings,
                "treasury_stock": treasury_stock,
                "goodwill": goodwill,
                "deferred_assets": deferred_assets,
                "securities_valuation": securities_valuation,
                "land_revaluation": land_revaluation,
            }

        # 計算が完了したことを明示的に表示
        st.success(
            "計算が完了しました! 上部タブの「分配可能額結果」をクリックして結果を確認してください。"
        )

with tabs[1]:
    st.markdown(
        "<div class='sub-header'>分配可能額計算結果</div>", unsafe_allow_html=True
    )

    if st.session_state.results.get("distributable_amount", None) is not None:
        distributable_amount = st.session_state.results["distributable_amount"]

        # 結果のサマリーを表示
        # 日付の表示形式を修正
        fiscal_year_end = st.session_state.results.get("fiscal_year_end", "")
        fiscal_year_end_str = (
            fiscal_year_end.strftime("%Y年%m月%d日")
            if isinstance(fiscal_year_end, datetime)
            else str(fiscal_year_end)
        )

        st.markdown(
            f"""
        <div class='result-box'>
            <h3>分配可能額</h3>
            <h2 class='{"positive" if distributable_amount >= 0 else "negative"}'>{format_yen(distributable_amount)}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # 計算過程の詳細を表示
        st.markdown(
            "<div class='section-header'>計算過程の詳細</div>", unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### 1. 剰余金の額の計算")
            st.markdown(
                f"""
            基本剰余金額: {format_yen(st.session_state.results.get('surplus_amount', 0))}
            <br><span class="reference">（会社法第446条）</span>
            """,
                unsafe_allow_html=True,
            )

            if calculation_mode == "詳細モード（全項目）":
                adjustments = [
                    (
                        "自己株式処分・消却による修正",
                        st.session_state.results.get("treasury_stock_adjustments", 0),
                    ),
                    (
                        "資本金・準備金の増減による修正",
                        st.session_state.results.get("capital_reserve_adjustments", 0),
                    ),
                    (
                        "配当による修正",
                        st.session_state.results.get("dividend_adjustments", 0),
                    ),
                ]

                for name, value in adjustments:
                    st.markdown(
                        f"{name}: {format_yen(value)} <span class='{'positive' if value >= 0 else 'negative'}'></span>",  # noqa
                        unsafe_allow_html=True,
                    )

            st.markdown("##### 2. 自己株式についての調整")
            st.markdown(
                f"""
            自己株式の帳簿価額: {format_yen(-st.session_state.results.get('treasury_stock_abs', 0))}
            <br><span class="reference">（会社法第461条第2項第3号）</span>
            """,
                unsafe_allow_html=True,
            )

            if calculation_mode == "詳細モード（全項目）":
                st.markdown(
                    f"""
                自己株式処分対価の調整: {format_yen(st.session_state.results.get('additional_treasury_adjustments', 0))}
                <br><span class="reference">（会社法第461条第2項第4号）</span>
                """,
                    unsafe_allow_html=True,
                )

        with col2:
            st.markdown("##### 3. 臨時決算に伴う調整")

            if st.session_state.results.get("interim_settlement_adjustments", 0) != 0:
                st.markdown(
                    f"""
                臨時決算による調整: {format_yen(st.session_state.results.get('interim_settlement_adjustments', 0))}
                <br><span class="reference">（会社法第461条第2項第2号、第5号）</span>
                """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("臨時決算は実施されていません。")

            st.markdown("##### 4. その他の調整")

            other_adjustments = [
                (
                    "のれん等調整額の控除",
                    -st.session_state.results.get("goodwill_deferred_deduction", 0),
                    "会社計算規則第158条第1号",
                ),
                (
                    "評価換算差額等の調整",
                    st.session_state.results.get("valuation_adjustments", 0),
                    "会社計算規則第158条第2号、第3号",
                ),
                (
                    "純資産額300万円維持の調整",
                    -st.session_state.results.get("net_assets_adjustment", 0),
                    "会社計算規則第158条第6号",
                ),
            ]

            for name, value, ref in other_adjustments:
                st.markdown(
                    f"""
                {name}: {format_yen(value)} <span class='{'positive' if value >= 0 else 'negative'}'></span>
                <br><span class="reference">（{ref}）</span>
                """,
                    unsafe_allow_html=True,
                )

        # 計算式の表示
        st.markdown(
            "<div class='section-header'>分配可能額の計算式</div>",
            unsafe_allow_html=True,
        )

        formula_parts = [
            f"剰余金の額 {format_yen(st.session_state.results.get('surplus_amount', 0))}",
            f"自己株式処分・消却修正 ({format_yen(st.session_state.results.get('treasury_stock_adjustments', 0))})",  # noqa
            f"資本金・準備金修正 ({format_yen(st.session_state.results.get('capital_reserve_adjustments', 0))})",  # noqa
            f"配当修正 ({format_yen(st.session_state.results.get('dividend_adjustments', 0))})",  # noqa
            f"自己株式帳簿価額 (-{format_yen(st.session_state.results.get('treasury_stock_abs', 0))})",  # noqa
            f"自己株式処分対価調整 ({format_yen(st.session_state.results.get('additional_treasury_adjustments', 0))})",  # noqa
            f"臨時決算調整 ({format_yen(st.session_state.results.get('interim_settlement_adjustments', 0))})",  # noqa
            f"のれん等調整額控除 (-{format_yen(st.session_state.results.get('goodwill_deferred_deduction', 0))})",  # noqa
            f"評価換算差額等調整 ({format_yen(st.session_state.results.get('valuation_adjustments', 0))})",  # noqa
            f"純資産額300万円維持調整 (-{format_yen(st.session_state.results.get('net_assets_adjustment', 0))})",  # noqa
        ]

        formula = "<br />　+ ".join(formula_parts)
        st.markdown(
            f"""
        <div class='info-box'>
        分配可能額<br />　= {formula}<br /> = <span class='{"positive" if distributable_amount >= 0 else "negative"}'>{format_yen(distributable_amount)}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # 注意事項の表示
        if distributable_amount < 0:
            st.markdown(
                """
            <div class='danger-box'>
            <strong>注意:</strong> 現在の状態では分配可能額がマイナスとなっており、配当や自己株式の有償取得を行うことができません。
            会社法では、分配可能額を超えて配当等が行われた場合、会社や債権者は株主に対して返還を請求することができます。
            また、当該行為に関する職務を行った取締役等も会社に対して支払い義務を負うことがあります。
            （会社法第462条、第463条）
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
            <div class='warning-box'>
            この分配可能額の範囲内で、配当や自己株式の有償取得を行うことが可能です。
            計算結果を実際の経営判断に利用する際は、専門家への相談をお勧めします。
            </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        st.info(
            "基本情報タブで必要な情報を入力し、「分配可能額を計算する」ボタンをクリックしてください。"
        )

with tabs[2]:
    st.markdown(
        "<div class='sub-header'>グラフによる分析</div>", unsafe_allow_html=True
    )

    if st.session_state.results.get("distributable_amount", None) is not None:
        # グラフの種類を選択
        graph_type = st.selectbox(
            "表示するグラフの種類を選択してください",
            [
                "分配可能額の構成要素",
                "純資産の構成",
                "のれん等調整額の影響",
                "分配可能額のウォーターフォールチャート",
            ],
        )

        if graph_type == "分配可能額の構成要素":
            # 分配可能額の構成要素の円グラフ
            components = {
                "その他資本剰余金": st.session_state.results.get(
                    "other_capital_surplus", 0
                ),
                "その他利益剰余金": st.session_state.results.get(
                    "other_retained_earnings", 0
                ),
                "自己株式の調整": -st.session_state.results.get("treasury_stock_abs", 0)
                + st.session_state.results.get("additional_treasury_adjustments", 0),
                "臨時決算の調整": st.session_state.results.get(
                    "interim_settlement_adjustments", 0
                ),
                "のれん等調整額": -st.session_state.results.get(
                    "goodwill_deferred_deduction", 0
                ),
                "評価換算差額等": st.session_state.results.get(
                    "valuation_adjustments", 0
                ),
                "その他の調整": -st.session_state.results.get(
                    "net_assets_adjustment", 0
                ),
            }

            # マイナス値を持つ項目を除外
            positive_components = {k: v for k, v in components.items() if v > 0}
            negative_components = {k: abs(v) for k, v in components.items() if v < 0}

            fig1 = px.pie(
                values=list(positive_components.values()),
                names=list(positive_components.keys()),
                title="分配可能額のプラス要素",
                color_discrete_sequence=px.colors.sequential.Blues_r,
            )

            fig2 = px.pie(
                values=list(negative_components.values()),
                names=list(negative_components.keys()),
                title="分配可能額のマイナス要素",
                color_discrete_sequence=px.colors.sequential.Reds_r,
            )

            col1, col2 = st.columns(2)

            with col1:
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                st.plotly_chart(fig2, use_container_width=True)

        elif graph_type == "純資産の構成":
            # 純資産の構成の棒グラフ
            equity_components = {
                "資本金": st.session_state.results.get("capital_stock", 0),
                "資本準備金": st.session_state.results.get("capital_reserve", 0),
                "利益準備金": st.session_state.results.get("earned_reserve", 0),
                "その他資本剰余金": st.session_state.results.get(
                    "other_capital_surplus", 0
                ),
                "その他利益剰余金": st.session_state.results.get(
                    "other_retained_earnings", 0
                ),
                "自己株式": st.session_state.results.get("treasury_stock", 0),
                "評価・換算差額等": st.session_state.results.get(
                    "securities_valuation", 0
                )
                + st.session_state.results.get("land_revaluation", 0),
            }

            df = pd.DataFrame(
                {
                    "項目": list(equity_components.keys()),
                    "金額": list(equity_components.values()),
                }
            )

            fig = px.bar(
                df,
                x="項目",
                y="金額",
                title="純資産の構成",
                color="金額",
                color_continuous_scale=px.colors.diverging.RdBu,
                text_auto=True,
            )

            fig.update_layout(yaxis_title="金額（円）")
            st.plotly_chart(fig, use_container_width=True)

        elif graph_type == "のれん等調整額の影響":
            # のれん等調整額の影響の積み上げ棒グラフ
            goodwill_half = int(st.session_state.results.get("goodwill", 0) / 2)
            deferred = st.session_state.results.get("deferred_assets", 0)
            deduction = st.session_state.results.get("goodwill_deferred_deduction", 0)

            # 資本金と準備金の合計を取得
            capital_stock = st.session_state.results.get("capital_stock", 0)
            capital_reserve = st.session_state.results.get("capital_reserve", 0)
            earned_reserve = st.session_state.results.get("earned_reserve", 0)
            other_capital_surplus = st.session_state.results.get(
                "other_capital_surplus", 0
            )

            # 資本金＋準備金の合計
            capital_reserves_total = capital_stock + capital_reserve + earned_reserve

            df = pd.DataFrame(
                {
                    "項目": ["資本金・準備金等", "のれん等調整額", "実際の控除額"],
                    "資本金・準備金": [capital_reserves_total, 0, 0],
                    "その他資本剰余金": [other_capital_surplus, 0, 0],
                    "のれん÷2": [0, goodwill_half, 0],
                    "繰延資産": [0, deferred, 0],
                    "控除額": [0, 0, deduction],
                }
            )

            fig = go.Figure(
                data=[
                    go.Bar(
                        name="資本金・準備金",
                        x=df["項目"],
                        y=df["資本金・準備金"],
                        marker_color="#81C784",
                    ),
                    go.Bar(
                        name="その他資本剰余金",
                        x=df["項目"],
                        y=df["その他資本剰余金"],
                        marker_color="#4CAF50",
                    ),
                    go.Bar(
                        name="のれん÷2",
                        x=df["項目"],
                        y=df["のれん÷2"],
                        marker_color="#90CAF9",
                    ),
                    go.Bar(
                        name="繰延資産",
                        x=df["項目"],
                        y=df["繰延資産"],
                        marker_color="#42A5F5",
                    ),
                    go.Bar(
                        name="控除額",
                        x=df["項目"],
                        y=df["控除額"],
                        marker_color="#1976D2",
                    ),
                ]
            )

            fig.update_layout(
                title="のれん等調整額と資本金・準備金の比較",
                barmode="stack",
                yaxis_title="金額（円）",
            )

            st.plotly_chart(fig, use_container_width=True)

            # 計算過程の説明
            # 該当するパターンを特定
            goodwill_deferred_total = goodwill_half + deferred
            if goodwill_deferred_total <= capital_reserves_total:
                pattern = "パターン1"
            elif (
                goodwill_deferred_total
                <= capital_reserves_total + other_capital_surplus
            ):
                pattern = "パターン2"
            elif goodwill_half <= capital_reserves_total + other_capital_surplus:
                pattern = "パターン3"
            else:
                pattern = "パターン4"

            # パターンごとの詳細説明
            if pattern == "パターン1":
                st.markdown(
                    f"""
                <div class='info-box'>
                <p><strong>■ のれん等調整額の計算結果</strong></p>
                <p>のれん等調整額（{format_yen(goodwill_deferred_total)}）が資本金・準備金の合計（{format_yen(capital_reserves_total)}）以下のため、<span class="positive">控除は不要</span>です。</p>

                <p><strong>■ 計算過程</strong></p>
                <p>{format_yen(goodwill_deferred_total)} ≤ {format_yen(capital_reserves_total)} なので、控除額 = 0円</p>

                <p><strong>■ 解説</strong></p>
                <p>のれん等調整額が資本金・準備金の合計額の範囲内に収まっているため、分配可能額からの控除は発生しません。この場合、のれんや繰延資産があっても分配可能額への影響はありません。</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            elif pattern == "パターン2":
                excess_amount = goodwill_deferred_total - capital_reserves_total
                st.markdown(
                    f"""
                <div class='info-box'>
                <p><strong>■ のれん等調整額の計算結果</strong></p>
                <p>のれん等調整額（{format_yen(goodwill_deferred_total)}）が資本金・準備金の合計（{format_yen(capital_reserves_total)}）を超えていますが、資本金・準備金の合計とその他資本剰余金の合計（{format_yen(capital_reserves_total + other_capital_surplus)}）以下です。</p>

                <p><strong>■ 計算過程</strong></p>
                <p>控除額 = のれん等調整額 - 資本金・準備金の合計</p>
                <p>控除額 = {format_yen(goodwill_deferred_total)} - {format_yen(capital_reserves_total)} = {format_yen(excess_amount)}</p>

                <p><strong>■ 解説</strong></p>
                <p>のれん等調整額のうち、資本金・準備金の合計を超える部分（{format_yen(excess_amount)}）だけが分配可能額から控除されます。この金額は分配不可となります。</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            elif pattern == "パターン3":
                excess_amount = goodwill_deferred_total - capital_reserves_total
                st.markdown(
                    f"""
                <div class='info-box'>
                <p><strong>■ のれん等調整額の計算結果</strong></p>
                <p>のれん等調整額（{format_yen(goodwill_deferred_total)}）が資本金・準備金の合計（{format_yen(capital_reserves_total)}）を超えていますが、のれんの半額が資本金・準備金の合計とその他資本剰余金の合計（{format_yen(capital_reserves_total + other_capital_surplus)}）以下です。</p>

                <p><strong>■ 計算過程</strong></p>
                <p>控除額 = のれん等調整額 - 資本金・準備金の合計</p>
                <p>控除額 = {format_yen(goodwill_deferred_total)} - {format_yen(capital_reserves_total)} = {format_yen(excess_amount)}</p>

                <p><strong>■ 解説</strong></p>
                <p>のれん等調整額のうち、資本金・準備金の合計を超える部分（{format_yen(excess_amount)}）が分配可能額から控除されます。この場合、のれんは資本剰余金の範囲内で処理できるため、超過分だけが控除対象となります。</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            else:  # パターン4
                final_deduction = other_capital_surplus + deferred
                st.markdown(
                    f"""
                <div class='info-box'>
                <p><strong>■ のれん等調整額の計算結果</strong></p>
                <p>のれんの半額（{format_yen(goodwill_half)}）が資本金・準備金の合計とその他資本剰余金の合計（{format_yen(capital_reserves_total + other_capital_surplus)}）を超えています。</p>

                <p><strong>■ 計算過程</strong></p>
                <p>控除額 = その他資本剰余金 + 繰延資産の額</p>
                <p>控除額 = {format_yen(other_capital_surplus)} + {format_yen(deferred)} = {format_yen(final_deduction)}</p>

                <p><strong>■ 解説</strong></p>
                <p>この場合、のれんの控除額はその他資本剰余金を上限とし、それに繰延資産の全額を加えた金額（{format_yen(final_deduction)}）が分配可能額から控除されます。のれんの一部は資本金・準備金でカバーされるため、控除対象はその他資本剰余金の範囲内となります。</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        elif graph_type == "分配可能額のウォーターフォールチャート":
            # 分配可能額の計算過程をウォーターフォールチャートで表示
            base_surplus = st.session_state.results.get("surplus_amount", 0)
            treasury_adj = st.session_state.results.get("treasury_stock_adjustments", 0)
            capital_adj = st.session_state.results.get("capital_reserve_adjustments", 0)
            dividend_adj = st.session_state.results.get("dividend_adjustments", 0)
            treasury_book = -st.session_state.results.get("treasury_stock_abs", 0)
            disposal_adj = st.session_state.results.get(
                "additional_treasury_adjustments", 0
            )
            interim_adj = st.session_state.results.get(
                "interim_settlement_adjustments", 0
            )
            goodwill_adj = -st.session_state.results.get(
                "goodwill_deferred_deduction", 0
            )
            valuation_adj = st.session_state.results.get("valuation_adjustments", 0)
            net_assets_adj = -st.session_state.results.get("net_assets_adjustment", 0)
            final = st.session_state.results.get("distributable_amount", 0)

            # 計算ステップの定義
            steps = [
                "剰余金の額",
                "自己株式処分・消却",
                "資本金・準備金調整",
                "配当修正",
                "自己株式帳簿価額",
                "自己株式処分対価",
                "臨時決算調整",
                "のれん等調整額",
                "評価換算差額等",
                "純資産300万円維持",
                "分配可能額",
            ]

            # 各ステップの値の定義
            values = [
                base_surplus,  # 始点
                treasury_adj,
                capital_adj,
                dividend_adj,
                treasury_book,
                disposal_adj,
                interim_adj,
                goodwill_adj,
                valuation_adj,
                net_assets_adj,
                None,  # 最終的な分配可能額（自動計算される）
            ]

            # 累積値の計算
            cumulative = base_surplus
            measure = ["absolute"]  # 最初は絶対値

            for i in range(1, len(values) - 1):
                if values[i] is not None:  # None以外の値の場合
                    cumulative += values[i]
                    measure.append("relative")

            measure.append("total")  # 最後は合計
            values[-1] = final  # 最終値をセット

            # ウォーターフォールチャートの作成
            fig = go.Figure(
                go.Waterfall(
                    name="分配可能額計算",
                    orientation="v",
                    measure=measure,
                    x=steps,
                    textposition="outside",
                    text=[f"{v:,}円" if v is not None else "" for v in values],
                    y=values,
                    connector={"line": {"color": "rgb(63, 63, 63)"}},
                    decreasing={"marker": {"color": "#EF5350"}},
                    increasing={"marker": {"color": "#66BB6A"}},
                    totals={"marker": {"color": "#42A5F5"}},
                )
            )

            fig.update_layout(
                title="分配可能額の計算過程", showlegend=False, yaxis_title="金額（円）"
            )

            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(
            "基本情報タブで必要な情報を入力し、「分配可能額を計算する」ボタンをクリックしてください。"
        )
