"""
MBR Automation System - Basic Workflow Test
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.ingestion.excel_reader import ExcelDataReader
from src.transformation.calculator import DataAggregator, MetricCalculator
from src.validation.validator import DataValidator
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main test function"""
    print("=" * 60)
    print("MBR Automation System - Basic Workflow Test")
    print("=" * 60)

    # Excel file path
    excel_file = Path("dec-25/MBR数据模板.xlsx")

    if not excel_file.exists():
        print(f"\nError: Excel file not found: {excel_file}")
        print("Please ensure the file path is correct")
        return

    try:
        # Step 1: Read Excel data
        print("\n[Step 1] Reading Excel data...")
        reader = ExcelDataReader(excel_file)
        data = reader.parse_all()

        print(f"  [OK] Successfully read data")
        print(f"  - Report period: {data.report_period}")
        print(f"  - Brand: {data.brand}")
        print(f"  - Daily metrics: {len(data.target_metrics)}")
        print(f"  - Campaigns: {len(data.campaigns)}")

        # Step 2: Data aggregation
        print("\n[Step 2] Aggregating monthly data...")
        if data.target_metrics:
            aggregator = DataAggregator(data.target_metrics)

            # Calculate all monthly metrics
            monthly_metrics = aggregator.calculate_all_monthly()
            print(f"  [OK] Calculated {len(monthly_metrics)} monthly metrics")

            # Calculate YoY growth
            monthly_metrics = aggregator.calculate_yoy_for_all(monthly_metrics)
            print(f"  [OK] Calculated YoY growth rates")

            # Calculate MoM growth
            monthly_metrics = aggregator.calculate_mom_for_all(monthly_metrics)
            print(f"  [OK] Calculated MoM growth rates")

            # Update report data
            data.monthly_metrics = monthly_metrics

            # Show sample monthly data
            print("\n  Sample monthly data (first 3):")
            for metric in monthly_metrics[:3]:
                yoy_str = f"{metric.yoy_growth:+.1f}%" if metric.yoy_growth else "N/A"
                print(f"    {metric.channel} {metric.period}: "
                      f"NET={metric.net:,.0f}, YoY={yoy_str}")

        # Step 3: Data validation
        print("\n[Step 3] Validating data quality...")
        validator = DataValidator(strict_mode=False)
        validation_result = validator.validate_report_data(data)

        print(f"  Validation results:")
        print(f"  - Passed: {'[OK] Yes' if validation_result.is_valid else '[FAIL] No'}")
        print(f"  - Errors: {len(validation_result.errors)}")
        print(f"  - Warnings: {len(validation_result.warnings)}")
        print(f"  - Quality score: {validation_result.score:.1f}/100")

        if validation_result.errors:
            print(f"\n  Error details:")
            for error in validation_result.errors[:3]:
                print(f"    [X] {error}")
            if len(validation_result.errors) > 3:
                print(f"    ... and {len(validation_result.errors) - 3} more errors")

        if validation_result.warnings:
            print(f"\n  Warning details:")
            for warning in validation_result.warnings[:3]:
                print(f"    [!] {warning}")
            if len(validation_result.warnings) > 3:
                print(f"    ... and {len(validation_result.warnings) - 3} more warnings")

        # Step 4: Data statistics
        print("\n[Step 4] Data statistics summary...")

        if data.target_metrics:
            # Statistics by channel
            channels = {}
            for metric in data.target_metrics:
                ch = metric.channel.value
                if ch not in channels:
                    channels[ch] = {'net': 0, 'gmv': 0, 'uv': 0}
                channels[ch]['net'] += metric.net or 0
                channels[ch]['gmv'] += metric.gmv or 0
                channels[ch]['uv'] += metric.uv or 0

            print(f"\n  Summary by channel:")
            for channel, stats in sorted(channels.items()):
                print(f"    {channel}:")
                print(f"      - GMV: {stats['gmv']:,.0f}")
                print(f"      - NET: {stats['net']:,.0f}")
                print(f"      - UV: {stats['uv']:,.0f}")

        # Step 5: Calculator examples
        print("\n[Step 5] Calculator function demos...")

        # YoY calculation
        yoy = MetricCalculator.calculate_yoy(1500000, 1000000)
        print(f"  YoY calculation example:")
        print(f"    Current period: 1,500,000")
        print(f"    Last year period: 1,000,000")
        print(f"    YoY growth: {yoy:+.1f}%")

        # MoM calculation
        mom = MetricCalculator.calculate_mom(120000, 100000)
        print(f"\n  MoM calculation example:")
        print(f"    Current month: 120,000")
        print(f"    Last month: 100,000")
        print(f"    MoM growth: {mom:+.1f}%")

        # CR calculation
        cr = MetricCalculator.calculate_cr(500, 10000)
        print(f"\n  CR calculation example:")
        print(f"    Buyers: 500")
        print(f"    UV: 10,000")
        print(f"    Conversion rate: {cr:.2f}%")

        # Complete message
        print("\n" + "=" * 60)
        print("Test completed!")
        print("=" * 60)

        if validation_result.is_valid:
            print("\n[OK] Data validation passed, ready for next steps")
        else:
            print("\n[!] Data validation not fully passed, please check errors")

    except Exception as e:
        print(f"\n[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\nNote: This is Phase 1 basic functionality test")
    print("Next steps: Phase 2 (AI Insights) -> Phase 3 (PPT Generation) -> Phase 4 (Claude Skill)")


if __name__ == "__main__":
    main()
