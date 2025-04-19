import math

import pytest


# 分配可能額計算関数（アプリのロジックを分離したもの）
def calculate_distributable_amount(
    # 会社の基本情報
    capital_stock=0,
    capital_reserve=0,
    other_capital_surplus=0,
    earned_reserve=0,
    other_retained_earnings=0,
    treasury_stock=0,
    # のれん・繰延資産
    goodwill=0,
    deferred_assets=0,
    # 評価・換算差額等
    securities_valuation=0,
    land_revaluation=0,
    # 自己株式の処分・消却
    disposal_treasury_stock=0,
    disposal_consideration=0,
    canceled_treasury_stock=0,
    # 資本金・準備金の増減
    capital_reduction=0,
    reserve_reduction=0,
    surplus_to_capital=0,
    # 剰余金の配当
    dividend_amount=0,
    dividend_reserve=0,
    # 臨時決算の情報
    interim_settlement=False,
    interim_profit=0,
    interim_loss=0,
    interim_treasury_disposal=0,
):
    # 1. 剰余金の額の計算
    surplus_amount = other_capital_surplus + other_retained_earnings

    # 2. 剰余金の額の調整
    treasury_stock_adjustments = (
        disposal_consideration - disposal_treasury_stock - canceled_treasury_stock
    )
    capital_reserve_adjustments = (
        capital_reduction + reserve_reduction - surplus_to_capital
    )
    dividend_adjustments = -(dividend_amount + dividend_reserve)

    # 3. 自己株式についての調整
    treasury_stock_abs = abs(treasury_stock) - disposal_treasury_stock
    additional_treasury_adjustments = -disposal_consideration

    # 4. 臨時決算に伴う調整
    interim_settlement_adjustments = 0
    if interim_settlement:
        interim_settlement_adjustments = (
            interim_profit - interim_loss + interim_treasury_disposal
        )

    # 5. のれん等調整額の計算
    goodwill_adjustment = math.floor(goodwill / 2)
    deferred_asset_adjustment = deferred_assets
    goodwill_deferred_adjustment = goodwill_adjustment + deferred_asset_adjustment

    # 資本金と準備金の合計
    capital_reserve_total = capital_stock + capital_reserve + earned_reserve

    # のれん等調整額の分配可能額からの控除額計算
    if goodwill_deferred_adjustment <= capital_reserve_total:
        goodwill_deferred_deduction = 0
    elif goodwill_deferred_adjustment <= capital_reserve_total + other_capital_surplus:
        goodwill_deferred_deduction = (
            goodwill_deferred_adjustment - capital_reserve_total
        )
    elif goodwill_adjustment <= capital_reserve_total + other_capital_surplus:
        goodwill_deferred_deduction = (
            goodwill_deferred_adjustment - capital_reserve_total
        )
    else:
        goodwill_deferred_deduction = other_capital_surplus + deferred_asset_adjustment

    # 6. 評価換算差額等の調整
    valuation_adjustments = 0
    if securities_valuation < 0:
        valuation_adjustments -= abs(securities_valuation)
    if land_revaluation < 0:
        valuation_adjustments -= abs(land_revaluation)

    # 7. 純資産額300万円維持のための調整
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

    # 8. 分配可能額の計算
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

    return {
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
    }


# テストケース
class TestDistributableAmount:

    # 基本的なケース
    def test_basic_case(self):
        result = calculate_distributable_amount(
            capital_stock=10000000,
            capital_reserve=5000000,
            other_capital_surplus=3000000,
            earned_reserve=2000000,
            other_retained_earnings=20000000,
            treasury_stock=-2000000,
        )

        # 剰余金の額 = その他資本剰余金 + その他利益剰余金
        assert result["surplus_amount"] == 23000000

        # 自己株式の帳簿価額の控除
        assert result["treasury_stock_abs"] == 2000000

        # 分配可能額の計算結果
        assert result["distributable_amount"] == 21000000  # 23,000,000 - 2,000,000

    # のれん等調整額のケース
    def test_goodwill_adjustment(self):
        # ケース1: のれん等調整額が資本金+準備金以下
        result1 = calculate_distributable_amount(
            capital_stock=10000000,
            capital_reserve=5000000,
            earned_reserve=2000000,
            other_capital_surplus=3000000,
            other_retained_earnings=20000000,
            goodwill=20000000,  # のれん÷2 = 10,000,000
            deferred_assets=5000000,  # 合計15,000,000 < 17,000,000(資本金+準備金)
        )
        assert result1["goodwill_deferred_deduction"] == 0

        # ケース2: のれん等調整額が資本金+準備金を超え、資本金+準備金+その他資本剰余金以下
        result2 = calculate_distributable_amount(
            capital_stock=10000000,
            capital_reserve=5000000,
            earned_reserve=2000000,
            other_capital_surplus=3000000,
            other_retained_earnings=20000000,
            goodwill=30000000,  # のれん÷2 = 15,000,000
            deferred_assets=5000000,  # 合計20,000,000 > 17,000,000, <= 20,000,000
        )
        assert (
            result2["goodwill_deferred_deduction"] == 3000000
        )  # 20,000,000 - 17,000,000

        # ケース3: のれん等調整額が資本金+準備金+その他資本剰余金を超え、のれん÷2が以下
        result3 = calculate_distributable_amount(
            capital_stock=10000000,
            capital_reserve=5000000,
            earned_reserve=2000000,
            other_capital_surplus=3000000,
            other_retained_earnings=20000000,
            goodwill=30000000,  # のれん÷2 = 15,000,000
            deferred_assets=10000000,  # 合計25,000,000 > 20,000,000, のれん÷2は15,000,000 < 20,000,000 # noqa
        )
        assert (
            result3["goodwill_deferred_deduction"] == 8000000
        )  # 25,000,000 - 17,000,000

        # ケース4: のれん÷2が資本金+準備金+その他資本剰余金を超える
        result4 = calculate_distributable_amount(
            capital_stock=10000000,
            capital_reserve=5000000,
            earned_reserve=2000000,
            other_capital_surplus=3000000,
            other_retained_earnings=20000000,
            goodwill=50000000,  # のれん÷2 = 25,000,000 > 20,000,000
            deferred_assets=10000000,
        )
        assert (
            result4["goodwill_deferred_deduction"] == 13000000
        )  # その他資本剰余金 + 繰延資産

    # 評価換算差額のケース
    def test_valuation_adjustment(self):
        result = calculate_distributable_amount(
            capital_stock=10000000,
            other_capital_surplus=3000000,
            other_retained_earnings=20000000,
            securities_valuation=-2000000,
            land_revaluation=-3000000,
        )
        assert result["valuation_adjustments"] == -5000000

    # 純資産額300万円維持のケース
    def test_minimum_net_assets(self):
        # 純資産額が300万円未満のケース
        result1 = calculate_distributable_amount(
            capital_stock=1000000,
            other_capital_surplus=1000000,
            other_retained_earnings=-500000,
            treasury_stock=-200000,
        )
        assert (
            result1["net_assets_adjustment"] == 1700000
        )  # 3,000,000 - (1,000,000 + 1,000,000 - 500,000 - 200,000)

        # 純資産額が300万円以上のケース
        result2 = calculate_distributable_amount(
            capital_stock=2000000,
            other_capital_surplus=1000000,
            other_retained_earnings=1000000,
        )
        assert result2["net_assets_adjustment"] == 0

    # 自己株式処分・消却のケース
    def test_treasury_stock_adjustments(self):
        result = calculate_distributable_amount(
            other_capital_surplus=3000000,
            other_retained_earnings=10000000,
            treasury_stock=-5000000,
            disposal_treasury_stock=2000000,
            disposal_consideration=2500000,
            canceled_treasury_stock=1000000,
        )
        assert (
            result["treasury_stock_adjustments"] == -500000
        )  # 2,500,000 - 2,000,000 - 1,000,000
        assert result["additional_treasury_adjustments"] == -2500000

    # 資本金・準備金の増減のケース
    def test_capital_reserve_adjustments(self):
        result = calculate_distributable_amount(
            other_capital_surplus=3000000,
            other_retained_earnings=10000000,
            capital_reduction=5000000,
            reserve_reduction=3000000,
            surplus_to_capital=2000000,
        )
        assert (
            result["capital_reserve_adjustments"] == 6000000
        )  # 5,000,000 + 3,000,000 - 2,000,000

    # 剰余金の配当のケース
    def test_dividend_adjustments(self):
        result = calculate_distributable_amount(
            other_capital_surplus=3000000,
            other_retained_earnings=10000000,
            dividend_amount=2000000,
            dividend_reserve=200000,
        )
        assert result["dividend_adjustments"] == -2200000  # -(2,000,000 + 200,000)

    # 臨時決算のケース
    def test_interim_settlement(self):
        # 臨時決算なしのケース
        result1 = calculate_distributable_amount(
            other_capital_surplus=3000000, other_retained_earnings=10000000
        )
        assert result1["interim_settlement_adjustments"] == 0

        # 臨時決算ありのケース（利益あり）
        result2 = calculate_distributable_amount(
            other_capital_surplus=3000000,
            other_retained_earnings=10000000,
            interim_settlement=True,
            interim_profit=5000000,
            interim_loss=0,
            interim_treasury_disposal=1000000,
        )
        assert (
            result2["interim_settlement_adjustments"] == 6000000
        )  # 5,000,000 + 1,000,000

        # 臨時決算ありのケース（損失あり）
        result3 = calculate_distributable_amount(
            other_capital_surplus=3000000,
            other_retained_earnings=10000000,
            interim_settlement=True,
            interim_profit=0,
            interim_loss=2000000,
            interim_treasury_disposal=1000000,
        )
        assert (
            result3["interim_settlement_adjustments"] == -1000000
        )  # -2,000,000 + 1,000,000

    # 複合ケース
    def test_complex_case(self):
        result = calculate_distributable_amount(
            capital_stock=10000000,
            capital_reserve=5000000,
            earned_reserve=2000000,
            other_capital_surplus=3000000,
            other_retained_earnings=20000000,
            treasury_stock=-3000000,
            goodwill=10000000,
            deferred_assets=2000000,
            securities_valuation=-1000000,
            disposal_treasury_stock=1000000,
            disposal_consideration=1200000,
            canceled_treasury_stock=500000,
            capital_reduction=2000000,
            reserve_reduction=1000000,
            surplus_to_capital=500000,
            dividend_amount=1500000,
            dividend_reserve=150000,
            interim_settlement=True,
            interim_profit=3000000,
            interim_loss=500000,
            interim_treasury_disposal=800000,
        )

        # 各調整値の確認
        assert result["surplus_amount"] == 23000000
        assert result["treasury_stock_adjustments"] == -300000
        assert result["capital_reserve_adjustments"] == 2500000
        assert result["dividend_adjustments"] == -1650000
        assert result["treasury_stock_abs"] == 2000000
        assert result["additional_treasury_adjustments"] == -1200000
        assert result["interim_settlement_adjustments"] == 3300000

        # のれん等調整額の確認
        # のれん÷2 + 繰延資産 = 5,000,000 + 2,000,000 = 7,000,000
        # 資本金+準備金 = 17,000,000 > 7,000,000
        assert result["goodwill_deferred_deduction"] == 0

        assert result["valuation_adjustments"] == -1000000
        assert result["net_assets_adjustment"] == 0

        # 最終的な分配可能額
        expected = (
            23000000  # 剰余金の額
            - 300000  # 自己株式処分・消却修正
            + 2500000  # 資本金・準備金修正
            - 1650000  # 配当修正
            - 2000000  # 自己株式帳簿価額
            - 1200000  # 自己株式処分対価調整
            + 3300000  # 臨時決算調整
            - 0  # のれん等調整額控除
            - 1000000  # 評価換算差額等調整
            - 0  # 純資産額300万円維持調整
        )
        assert result["distributable_amount"] == expected

    # 純資産額がちょうど300万円の場合のテスト
    def test_exact_minimum_net_assets(self):
        result = calculate_distributable_amount(
            capital_stock=3000000, other_capital_surplus=0, other_retained_earnings=0
        )
        assert result["net_assets_adjustment"] == 0
        assert result["distributable_amount"] == 0

    # のれん等調整額の境界値テスト
    def test_edge_cases_goodwill(self):
        # 資本金+準備金とのれん等調整額が同額の場合
        result = calculate_distributable_amount(
            capital_stock=5000000,
            capital_reserve=3000000,
            earned_reserve=2000000,
            other_capital_surplus=3000000,
            other_retained_earnings=10000000,
            goodwill=20000000,  # のれん÷2 = 10,000,000
            deferred_assets=0,  # 合計10,000,000 = 10,000,000(資本金+準備金)
        )
        assert result["goodwill_deferred_deduction"] == 0


# エッジケーステスト
def test_zero_values():
    """全ての値がゼロの場合のテスト"""
    result = calculate_distributable_amount()
    # 純資産額300万円維持のための調整により、分配可能額はマイナスになる
    assert result["distributable_amount"] == -3000000


def test_negative_retained_earnings():
    """その他利益剰余金がマイナスの場合のテスト"""
    result = calculate_distributable_amount(
        capital_stock=10000000,
        other_capital_surplus=5000000,
        other_retained_earnings=-8000000,
    )
    assert result["surplus_amount"] == -3000000
    assert result["distributable_amount"] == -3000000


def test_maximum_values():
    """大きな数値の場合のテスト"""
    result = calculate_distributable_amount(
        capital_stock=1000000000,
        capital_reserve=500000000,
        other_capital_surplus=300000000,
        earned_reserve=200000000,
        other_retained_earnings=2000000000,
    )
    assert result["distributable_amount"] == 2300000000


# 実行部分
if __name__ == "__main__":
    # テストを実行
    pytest.main(["-v"])
    # テストを実行
    pytest.main(["-v"])
