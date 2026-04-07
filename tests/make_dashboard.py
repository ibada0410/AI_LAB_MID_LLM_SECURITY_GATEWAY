# tests/make_complete_dashboard.py
import pandas as pd
import os
import glob
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO

print("=" * 60)
print("📊 Complete Dashboard Generator (HTML + Charts + PNG)")
print("=" * 60)

# Find CSV file
eval_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "eval_results")
csv_files = glob.glob(os.path.join(eval_dir, "*.csv"))

if not csv_files:
    print("❌ No CSV files found!")
    exit()

csv_path = csv_files[0]
print(f"✅ Found: {os.path.basename(csv_path)}")

# Read CSV
df = pd.read_csv(csv_path)
print(f"✅ Loaded {len(df)} rows")

# Calculate stats
total = len(df)
passed = len(df[df['Pass'] == 'Yes'])
failed = total - passed
accuracy = (passed / total) * 100
avg_latency = df['Latency_ms'].mean()
min_latency = df['Latency_ms'].min()
max_latency = df['Latency_ms'].max()

# Get counts
actions = df['Action'].value_counts()
categories = df['Scenario'].value_counts()

print(f"\n📊 Statistics:")
print(f"   Total Tests: {total}")
print(f"   Passed: {passed}")
print(f"   Failed: {failed}")
print(f"   Accuracy: {accuracy:.1f}%")
print(f"   Avg Latency: {avg_latency:.1f}ms")

# ========== CREATE PNG IMAGES ==========
print("\n📸 Creating PNG images...")

# Create images directory
img_dir = os.path.join(eval_dir, "images")
os.makedirs(img_dir, exist_ok=True)

# 1. Pass/Fail Pie Chart
fig1, ax1 = plt.subplots(figsize=(6, 5))
sizes = [passed, failed]
colors = ['#28a745', '#dc3545']
labels = [f'Passed ({passed})', f'Failed ({failed})']
ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
ax1.set_title('Test Results - Pass/Fail Distribution', fontsize=14, fontweight='bold')
plt.savefig(os.path.join(img_dir, '1_pass_fail_pie.png'), dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"   ✅ 1_pass_fail_pie.png")

# 2. Actions Pie Chart
fig2, ax2 = plt.subplots(figsize=(6, 5))
action_colors = []
for a in actions.index:
    if a == 'Allow':
        action_colors.append('#28a745')
    elif a == 'Block':
        action_colors.append('#dc3545')
    else:
        action_colors.append('#ffc107')
ax2.pie(actions.values, labels=actions.index, colors=action_colors, autopct='%1.1f%%', startangle=90)
ax2.set_title('Actions Distribution (Allow/Block/Mask)', fontsize=14, fontweight='bold')
plt.savefig(os.path.join(img_dir, '2_actions_pie.png'), dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"   ✅ 2_actions_pie.png")

# 3. Categories Bar Chart - VERTICAL with proper label spacing
plt.close('all')

fig3, ax3 = plt.subplots(figsize=(10, 6))

bars = ax3.bar(range(len(categories)), categories.values, color='#667eea', edgecolor='white', linewidth=2)
ax3.set_title('Test Categories Distribution', fontsize=14, fontweight='bold', pad=20)
ax3.set_xlabel('Category', labelpad=15)
ax3.set_ylabel('Number of Tests')
ax3.set_ylim(0, max(categories.values) + 2)

# Set x-tick labels with rotation and proper alignment
ax3.set_xticks(range(len(categories)))
ax3.set_xticklabels(categories.index, rotation=45, ha='right', fontsize=10)

# Add value labels on top of bars
for bar, val in zip(bars, categories.values):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, str(val), 
             ha='center', va='bottom', fontweight='bold', fontsize=10)

# Adjust layout to prevent label cutoff
plt.subplots_adjust(bottom=0.25)

file_path = os.path.join(img_dir, '3_categories_bar.png')
if os.path.exists(file_path):
    os.remove(file_path)

plt.savefig(file_path, dpi=150, facecolor='white')
plt.close()

if os.path.exists(file_path):
    file_size = os.path.getsize(file_path)
    print(f"   ✅ 3_categories_bar.png ({file_size} bytes)")
else:
    print(f"   ❌ ERROR: File was not created!")

# 4. Latency Line Chart
fig4, ax4 = plt.subplots(figsize=(10, 5))
ax4.plot(range(1, len(df) + 1), df['Latency_ms'], 'b-o', linewidth=2, markersize=8, markerfacecolor='white', markeredgecolor='#667eea', markeredgewidth=2)
ax4.axhline(y=avg_latency, color='r', linestyle='--', linewidth=2, label=f'Average: {avg_latency:.1f}ms')
ax4.set_title('Latency Performance by Test Case', fontsize=14, fontweight='bold')
ax4.set_xlabel('Test ID')
ax4.set_ylabel('Latency (ms)')
ax4.legend()
ax4.grid(True, alpha=0.3)
plt.savefig(os.path.join(img_dir, '4_latency_line.png'), dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"   ✅ 4_latency_line.png")

# 5. Combined Dashboard Image - VERTICAL categories bar chart
fig5, axes = plt.subplots(2, 2, figsize=(14, 10))
fig5.suptitle('LLM Security Gateway - Complete Test Results Dashboard', fontsize=16, fontweight='bold')

# Pass/Fail
axes[0, 0].pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
axes[0, 0].set_title('Pass/Fail Distribution', fontsize=12)

# Actions
axes[0, 1].pie(actions.values, labels=actions.index, colors=action_colors, autopct='%1.1f%%', startangle=90)
axes[0, 1].set_title('Actions Distribution', fontsize=12)

# Categories - VERTICAL bar chart with rotated labels
bars_combined = axes[1, 0].bar(range(len(categories)), categories.values, color='#667eea', edgecolor='white', linewidth=1)
axes[1, 0].set_title('Test Categories', fontsize=12)
axes[1, 0].set_xlabel('Category', fontsize=9)
axes[1, 0].set_ylabel('Number of Tests', fontsize=9)
axes[1, 0].set_xticks(range(len(categories)))
axes[1, 0].set_xticklabels(categories.index, rotation=45, ha='right', fontsize=8)
# Add value labels
for bar, val in zip(bars_combined, categories.values):
    axes[1, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, str(val), 
                    ha='center', va='bottom', fontsize=8, fontweight='bold')

# Latency
axes[1, 1].plot(range(1, len(df) + 1), df['Latency_ms'], 'b-o', linewidth=2)
axes[1, 1].axhline(y=avg_latency, color='r', linestyle='--', label=f'Avg: {avg_latency:.1f}ms')
axes[1, 1].set_title('Latency Performance', fontsize=12)
axes[1, 1].set_xlabel('Test ID')
axes[1, 1].set_ylabel('Latency (ms)')
axes[1, 1].legend()

plt.tight_layout()
combined_path = os.path.join(eval_dir, "dashboard_combined.png")
plt.savefig(combined_path, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"   ✅ dashboard_combined.png")

# ========== CREATE HTML WITH CHARTS ==========
print("\n📄 Creating HTML dashboard...")

# Convert PNGs to base64 for embedding
def image_to_base64(img_path):
    with open(img_path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

pass_fail_img = image_to_base64(os.path.join(img_dir, '1_pass_fail_pie.png'))
actions_img = image_to_base64(os.path.join(img_dir, '2_actions_pie.png'))
categories_img = image_to_base64(os.path.join(img_dir, '3_categories_bar.png'))
latency_img = image_to_base64(os.path.join(img_dir, '4_latency_line.png'))

html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>LLM Security Gateway - Complete Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}
        .header h1 {{ font-size: 2.5rem; margin-bottom: 10px; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .stat-number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{ color: #666; margin-top: 10px; }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .chart-card {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }}
        .chart-card h3 {{
            margin-bottom: 15px;
            color: #333;
            border-left: 4px solid #667eea;
            padding-left: 15px;
            text-align: left;
        }}
        .chart-card img {{
            max-width: 100%;
            height: auto;
            border-radius: 10px;
        }}
        .full-width {{ grid-column: span 2; }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background: #667eea;
            color: white;
        }}
        .Allow {{ color: #28a745; font-weight: bold; }}
        .Block {{ color: #dc3545; font-weight: bold; }}
        .Mask {{ color: #ffc107; font-weight: bold; }}
        .footer {{
            text-align: center;
            color: white;
            margin-top: 30px;
            padding: 20px;
        }}
        @media (max-width: 768px) {{
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .charts-grid {{ grid-template-columns: 1fr; }}
            .full-width {{ grid-column: span 1; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ LLM Security Gateway</h1>
            <p>Complete Test Results Dashboard | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card"><div class="stat-number">{total}</div><div class="stat-label">Total Tests</div></div>
            <div class="stat-card"><div class="stat-number" style="color: #28a745;">{passed}</div><div class="stat-label">Passed ✅</div></div>
            <div class="stat-card"><div class="stat-number" style="color: #dc3545;">{failed}</div><div class="stat-label">Failed ❌</div></div>
            <div class="stat-card"><div class="stat-number">{accuracy:.1f}%</div><div class="stat-label">Success Rate</div></div>
        </div>

        <div class="charts-grid">
            <div class="chart-card">
                <h3>📊 Pass/Fail Distribution</h3>
                <img src="data:image/png;base64,{pass_fail_img}" alt="Pass/Fail Pie Chart">
            </div>
            <div class="chart-card">
                <h3>🎯 Actions Distribution</h3>
                <img src="data:image/png;base64,{actions_img}" alt="Actions Pie Chart">
            </div>
            <div class="chart-card">
                <h3>📈 Test Categories</h3>
                <img src="data:image/png;base64,{categories_img}" alt="Categories Bar Chart">
            </div>
            <div class="chart-card">
                <h3>⚡ Latency Performance</h3>
                <img src="data:image/png;base64,{latency_img}" alt="Latency Line Chart">
            </div>
        </div>

        <div class="chart-card full-width">
            <h3>📋 Detailed Test Results</h3>
            <div style="overflow-x: auto; max-height: 400px;">
                {df.to_html(index=False, classes='test-table')}
            </div>
        </div>

        <div class="footer">
            <p>🔐 LLM Security Gateway | {accuracy:.1f}% Accuracy | {avg_latency:.1f}ms Avg Latency</p>
            <p>Total Tests: {total} | Passed: {passed} | Failed: {failed}</p>
        </div>
    </div>
</body>
</html>'''

# Save HTML
html_path = os.path.join(eval_dir, "complete_dashboard.html")
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\n✅ HTML Dashboard saved to: {html_path}")

print("\n" + "=" * 60)
print("🎉 COMPLETE! Generated files:")
print("=" * 60)
print(f"\n📊 HTML Dashboard:")
print(f"   {html_path}")
print(f"\n📸 PNG Images (in eval_results/images/):")
print(f"   1. 1_pass_fail_pie.png - Pass/Fail Pie Chart")
print(f"   2. 2_actions_pie.png - Actions Pie Chart")
print(f"   3. 3_categories_bar.png - Categories Bar Chart")
print(f"   4. 4_latency_line.png - Latency Line Chart")
print(f"   5. dashboard_combined.png - All charts combined")
print(f"\n📁 All files saved in: {eval_dir}")
print("\n" + "=" * 60)
print("✨ Done!")