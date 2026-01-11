#!/usr/bin/env python3
"""
ベンチマーク結果を分析して比較グラフを生成するスクリプト
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os
import sys
from pathlib import Path

# 日本語フォント設定
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_results(results_dir):
    """結果ファイルを読み込む"""
    http2_files = glob.glob(os.path.join(results_dir, 'http2_*.csv'))
    http3_files = glob.glob(os.path.join(results_dir, 'http3_*.csv'))
    
    dfs = []
    for file in http2_files + http3_files:
        df = pd.read_csv(file)
        dfs.append(df)
    
    if not dfs:
        print("No result files found!")
        return None
    
    return pd.concat(dfs, ignore_index=True)

def analyze_by_condition(df):
    """ネットワーク条件別に分析"""
    # 条件でグループ化
    grouped = df.groupby(['Protocol', 'NetworkDelay(ms)', 'NetworkLoss(%)'])
    
    stats = grouped.agg({
        'TTFB(ms)': ['mean', 'std', 'min', 'max'],
        'TotalTime(ms)': ['mean', 'std', 'min', 'max'],
        'Throughput(KB/s)': ['mean', 'std']
    }).reset_index()
    
    return stats

def plot_ttfb_comparison(df, output_dir):
    """TTFBの比較グラフ"""
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    
    # 遅延による影響
    delay_data = df[df['NetworkLoss(%)'] == 0].groupby(['Protocol', 'NetworkDelay(ms)'])['TTFB(ms)'].mean().reset_index()
    
    for protocol in ['HTTP/2.0', 'HTTP/3.0']:
        protocol_data = delay_data[delay_data['Protocol'] == protocol]
        axes[0].plot(protocol_data['NetworkDelay(ms)'], protocol_data['TTFB(ms)'], 
                    marker='o', label=protocol, linewidth=2)
    
    axes[0].set_xlabel('Network Delay (ms)', fontsize=12)
    axes[0].set_ylabel('Average TTFB (ms)', fontsize=12)
    axes[0].set_title('TTFB vs Network Delay', fontsize=14, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # パケット損失による影響
    loss_data = df[df['NetworkDelay(ms)'] == 0].groupby(['Protocol', 'NetworkLoss(%)'])['TTFB(ms)'].mean().reset_index()
    
    for protocol in ['HTTP/2.0', 'HTTP/3.0']:
        protocol_data = loss_data[loss_data['Protocol'] == protocol]
        axes[1].plot(protocol_data['NetworkLoss(%)'], protocol_data['TTFB(ms)'], 
                    marker='o', label=protocol, linewidth=2)
    
    axes[1].set_xlabel('Packet Loss Rate (%)', fontsize=12)
    axes[1].set_ylabel('Average TTFB (ms)', fontsize=12)
    axes[1].set_title('TTFB vs Packet Loss', fontsize=14, fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'ttfb_comparison.png'), dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir}/ttfb_comparison.png")
    plt.close()

def plot_throughput_comparison(df, output_dir):
    """スループットの比較グラフ"""
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    
    # 遅延による影響
    delay_data = df[df['NetworkLoss(%)'] == 0].groupby(['Protocol', 'NetworkDelay(ms)'])['Throughput(KB/s)'].mean().reset_index()
    
    for protocol in ['HTTP/2.0', 'HTTP/3.0']:
        protocol_data = delay_data[delay_data['Protocol'] == protocol]
        axes[0].plot(protocol_data['NetworkDelay(ms)'], protocol_data['Throughput(KB/s)'], 
                    marker='o', label=protocol, linewidth=2)
    
    axes[0].set_xlabel('Network Delay (ms)', fontsize=12)
    axes[0].set_ylabel('Average Throughput (KB/s)', fontsize=12)
    axes[0].set_title('Throughput vs Network Delay', fontsize=14, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # パケット損失による影響
    loss_data = df[df['NetworkDelay(ms)'] == 0].groupby(['Protocol', 'NetworkLoss(%)'])['Throughput(KB/s)'].mean().reset_index()
    
    for protocol in ['HTTP/2.0', 'HTTP/3.0']:
        protocol_data = loss_data[loss_data['Protocol'] == protocol]
        axes[1].plot(protocol_data['NetworkLoss(%)'], protocol_data['Throughput(KB/s)'], 
                    marker='o', label=protocol, linewidth=2)
    
    axes[1].set_xlabel('Packet Loss Rate (%)', fontsize=12)
    axes[1].set_ylabel('Average Throughput (KB/s)', fontsize=12)
    axes[1].set_title('Throughput vs Packet Loss', fontsize=14, fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'throughput_comparison.png'), dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir}/throughput_comparison.png")
    plt.close()

def plot_heatmap(df, output_dir):
    """ヒートマップで性能を可視化"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    for idx, protocol in enumerate(['HTTP/2.0', 'HTTP/3.0']):
        protocol_data = df[df['Protocol'] == protocol]
        pivot = protocol_data.pivot_table(
            values='TTFB(ms)', 
            index='NetworkDelay(ms)', 
            columns='NetworkLoss(%)', 
            aggfunc='mean'
        )
        
        sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd', ax=axes[idx], 
                   cbar_kws={'label': 'TTFB (ms)'})
        axes[idx].set_title(f'{protocol} - TTFB Heatmap', fontsize=14, fontweight='bold')
        axes[idx].set_xlabel('Packet Loss Rate (%)', fontsize=12)
        axes[idx].set_ylabel('Network Delay (ms)', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'ttfb_heatmap.png'), dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir}/ttfb_heatmap.png")
    plt.close()

def generate_summary_report(df, output_dir):
    """サマリーレポートを生成"""
    report_path = os.path.join(output_dir, 'summary_report.txt')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("HTTP/2 vs HTTP/3 Performance Comparison Report\n")
        f.write("=" * 80 + "\n\n")
        
        # 全体統計
        f.write("Overall Statistics:\n")
        f.write("-" * 80 + "\n")
        for protocol in ['HTTP/2.0', 'HTTP/3.0']:
            protocol_data = df[df['Protocol'] == protocol]
            f.write(f"\n{protocol}:\n")
            f.write(f"  Total Requests: {len(protocol_data)}\n")
            f.write(f"  TTFB (avg): {protocol_data['TTFB(ms)'].mean():.3f} ms\n")
            f.write(f"  TTFB (std): {protocol_data['TTFB(ms)'].std():.3f} ms\n")
            f.write(f"  Total Time (avg): {protocol_data['TotalTime(ms)'].mean():.3f} ms\n")
            f.write(f"  Throughput (avg): {protocol_data['Throughput(KB/s)'].mean():.2f} KB/s\n")
        
        # 条件別統計
        f.write("\n\nPerformance by Network Conditions:\n")
        f.write("-" * 80 + "\n")
        
        stats = analyze_by_condition(df)
        for _, row in stats.iterrows():
            f.write(f"\nProtocol: {row['Protocol']}, ")
            f.write(f"Delay: {row['NetworkDelay(ms)']}ms, ")
            f.write(f"Loss: {row['NetworkLoss(%)']}%\n")
            f.write(f"  TTFB: {row[('TTFB(ms)', 'mean')]:.3f} ± {row[('TTFB(ms)', 'std')]:.3f} ms\n")
            f.write(f"  Total Time: {row[('TotalTime(ms)', 'mean')]:.3f} ± {row[('TotalTime(ms)', 'std')]:.3f} ms\n")
            f.write(f"  Throughput: {row[('Throughput(KB/s)', 'mean')]:.2f} ± {row[('Throughput(KB/s)', 'std')]:.2f} KB/s\n")
        
        # 勝者判定
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("Winner Analysis:\n")
        f.write("=" * 80 + "\n")
        
        for delay in df['NetworkDelay(ms)'].unique():
            for loss in df['NetworkLoss(%)'].unique():
                condition_data = df[(df['NetworkDelay(ms)'] == delay) & (df['NetworkLoss(%)'] == loss)]
                if len(condition_data) == 0:
                    continue
                
                http2_ttfb = condition_data[condition_data['Protocol'] == 'HTTP/2.0']['TTFB(ms)'].mean()
                http3_ttfb = condition_data[condition_data['Protocol'] == 'HTTP/3.0']['TTFB(ms)'].mean()
                
                winner = 'HTTP/2.0' if http2_ttfb < http3_ttfb else 'HTTP/3.0'
                diff_pct = abs(http2_ttfb - http3_ttfb) / min(http2_ttfb, http3_ttfb) * 100
                
                f.write(f"\nDelay: {delay}ms, Loss: {loss}%\n")
                f.write(f"  Winner: {winner} (by {diff_pct:.1f}%)\n")
                f.write(f"  HTTP/2 TTFB: {http2_ttfb:.3f} ms\n")
                f.write(f"  HTTP/3 TTFB: {http3_ttfb:.3f} ms\n")
    
    print(f"Saved: {report_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py <results_directory>")
        sys.exit(1)
    
    results_dir = sys.argv[1]
    
    if not os.path.exists(results_dir):
        print(f"Error: Directory '{results_dir}' does not exist")
        sys.exit(1)
    
    print("Loading benchmark results...")
    df = load_results(results_dir)
    
    if df is None or len(df) == 0:
        print("No data to analyze")
        sys.exit(1)
    
    print(f"Loaded {len(df)} records")
    print(f"Protocols: {df['Protocol'].unique()}")
    print(f"Network conditions: {len(df.groupby(['NetworkDelay(ms)', 'NetworkLoss(%)']))} patterns")
    
    # グラフ出力ディレクトリ
    output_dir = os.path.join(results_dir, 'analysis')
    os.makedirs(output_dir, exist_ok=True)
    
    print("\nGenerating analysis...")
    plot_ttfb_comparison(df, output_dir)
    plot_throughput_comparison(df, output_dir)
    plot_heatmap(df, output_dir)
    generate_summary_report(df, output_dir)
    
    print("\n" + "=" * 80)
    print("Analysis completed!")
    print(f"Results saved to: {output_dir}")
    print("=" * 80)

if __name__ == '__main__':
    main()

