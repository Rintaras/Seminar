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
    """結果ファイルを読み込む（セッションディレクトリ構造対応）"""
    # 新しい構造: session_XXX/experiment_name/http2_results.csv
    http2_files = glob.glob(os.path.join(results_dir, '*/http2_results.csv'))
    http3_files = glob.glob(os.path.join(results_dir, '*/http3_results.csv'))
    
    # 旧構造も探す: http2_*.csv
    if not http2_files:
        http2_files = glob.glob(os.path.join(results_dir, 'http2_*.csv'))
    if not http3_files:
        http3_files = glob.glob(os.path.join(results_dir, 'http3_*.csv'))
    
    dfs = []
    for file in http2_files + http3_files:
        try:
            df = pd.read_csv(file)
            # ファイル名から実験名を抽出（オプション）
            exp_name = os.path.basename(os.path.dirname(file))
            if exp_name and exp_name != results_dir:
                df['Experiment'] = exp_name
            dfs.append(df)
        except Exception as e:
            print(f"Warning: Failed to load {file}: {e}")
    
    if not dfs:
        print("No result files found!")
        return None
    
    return pd.concat(dfs, ignore_index=True)

def analyze_by_condition(df):
    """ネットワーク条件別に分析"""
    # 条件でグループ化
    grouped = df.groupby(['Protocol', 'NetworkDelay(ms)', 'Bandwidth'])
    
    stats = grouped.agg({
        'TTFB(ms)': ['mean', 'std', 'min', 'max'],
        'TotalTime(ms)': ['mean', 'std', 'min', 'max'],
        'Throughput(KB/s)': ['mean', 'std']
    }).reset_index()
    
    return stats

def plot_ttfb_comparison(df, output_dir):
    """TTFBの比較グラフ"""
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    
    # データの特性を検出
    unique_bandwidths = df['Bandwidth'].unique()
    unique_delays = df['NetworkDelay(ms)'].unique()
    
    # 左側のグラフ: 遅延による影響
    # 帯域幅が複数ある場合は無制限のみ、1種類の場合はそれを使用
    if len(unique_bandwidths) > 1:
        # 帯域無制限のデータ
        delay_data = df[(df['Bandwidth'] == '0') | (df['Bandwidth'] == 0)].groupby(['Protocol', 'NetworkDelay(ms)'])['TTFB(ms)'].mean().reset_index()
        bandwidth_label = "Unlimited Bandwidth"
    else:
        # 帯域が1種類のみの場合、そのデータを使用
        delay_data = df.groupby(['Protocol', 'NetworkDelay(ms)'])['TTFB(ms)'].mean().reset_index()
        bandwidth_label = f"Bandwidth: {unique_bandwidths[0]}"
    
    for protocol in ['HTTP/2.0', 'HTTP/3.0']:
        protocol_data = delay_data[delay_data['Protocol'] == protocol]
        if not protocol_data.empty:
            axes[0].plot(protocol_data['NetworkDelay(ms)'], protocol_data['TTFB(ms)'], 
                        marker='o', label=protocol, linewidth=2)
    
    axes[0].set_xlabel('Network Delay (ms)', fontsize=12)
    axes[0].set_ylabel('Average TTFB (ms)', fontsize=12)
    axes[0].set_title(f'TTFB vs Network Delay ({bandwidth_label})', fontsize=14, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 右側のグラフ: 帯域幅または遅延による影響
    if len(unique_bandwidths) > 1:
        # 帯域幅が複数ある場合: 帯域幅による影響（遅延0msの場合）
        bandwidth_data = df[df['NetworkDelay(ms)'] == 0].copy()
        bandwidth_order = ['100mbit', '10mbit', '5mbit', '1mbit', '0']
        bandwidth_data['BandwidthOrder'] = bandwidth_data['Bandwidth'].apply(
            lambda x: bandwidth_order.index(str(x)) if str(x) in bandwidth_order else 999
        )
        bandwidth_data = bandwidth_data.sort_values('BandwidthOrder')
        
        bw_grouped = bandwidth_data.groupby(['Protocol', 'Bandwidth'])['TTFB(ms)'].mean().reset_index()
        
        for protocol in ['HTTP/2.0', 'HTTP/3.0']:
            protocol_data = bw_grouped[bw_grouped['Protocol'] == protocol]
            if not protocol_data.empty:
                axes[1].plot(range(len(protocol_data)), protocol_data['TTFB(ms)'], 
                            marker='o', label=protocol, linewidth=2)
        
        if not bw_grouped.empty:
            unique_bw = bw_grouped['Bandwidth'].unique()
            axes[1].set_xticks(range(len(unique_bw)))
            axes[1].set_xticklabels(unique_bw, rotation=45)
        
        axes[1].set_xlabel('Bandwidth Limit', fontsize=12)
        axes[1].set_ylabel('Average TTFB (ms)', fontsize=12)
        axes[1].set_title('TTFB vs Bandwidth (No Delay)', fontsize=14, fontweight='bold')
    else:
        # 帯域幅が1種類のみの場合: 遅延による詳細グラフ
        delay_detail = df.groupby(['Protocol', 'NetworkDelay(ms)'])['TTFB(ms)'].agg(['mean', 'std']).reset_index()
        
        for protocol in ['HTTP/2.0', 'HTTP/3.0']:
            protocol_data = delay_detail[delay_detail['Protocol'] == protocol]
            if not protocol_data.empty:
                axes[1].errorbar(protocol_data['NetworkDelay(ms)'], protocol_data['mean'], 
                               yerr=protocol_data['std'], marker='o', label=protocol, 
                               linewidth=2, capsize=5, alpha=0.7)
        
        axes[1].set_xlabel('Network Delay (ms)', fontsize=12)
        axes[1].set_ylabel('Average TTFB (ms)', fontsize=12)
        axes[1].set_title(f'TTFB with Error Bars ({unique_bandwidths[0]} bandwidth)', fontsize=14, fontweight='bold')
    
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'ttfb_comparison.png'), dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir}/ttfb_comparison.png")
    plt.close()

def plot_throughput_comparison(df, output_dir):
    """スループットの比較グラフ"""
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    
    # データの特性を検出
    unique_bandwidths = df['Bandwidth'].unique()
    unique_delays = df['NetworkDelay(ms)'].unique()
    
    # 左側のグラフ: 遅延による影響
    if len(unique_bandwidths) > 1:
        # 帯域無制限のデータ
        delay_data = df[(df['Bandwidth'] == '0') | (df['Bandwidth'] == 0)].groupby(['Protocol', 'NetworkDelay(ms)'])['Throughput(KB/s)'].mean().reset_index()
        bandwidth_label = "Unlimited Bandwidth"
    else:
        # 帯域が1種類のみの場合
        delay_data = df.groupby(['Protocol', 'NetworkDelay(ms)'])['Throughput(KB/s)'].mean().reset_index()
        bandwidth_label = f"Bandwidth: {unique_bandwidths[0]}"
    
    for protocol in ['HTTP/2.0', 'HTTP/3.0']:
        protocol_data = delay_data[delay_data['Protocol'] == protocol]
        if not protocol_data.empty:
            axes[0].plot(protocol_data['NetworkDelay(ms)'], protocol_data['Throughput(KB/s)'], 
                        marker='o', label=protocol, linewidth=2)
    
    axes[0].set_xlabel('Network Delay (ms)', fontsize=12)
    axes[0].set_ylabel('Average Throughput (KB/s)', fontsize=12)
    axes[0].set_title(f'Throughput vs Network Delay ({bandwidth_label})', fontsize=14, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 右側のグラフ: 帯域幅または遅延詳細
    if len(unique_bandwidths) > 1:
        # 帯域幅が複数ある場合: 帯域幅による影響（遅延0msの場合）
        bandwidth_data = df[df['NetworkDelay(ms)'] == 0].copy()
        bandwidth_order = ['100mbit', '10mbit', '5mbit', '1mbit', '0']
        bandwidth_data['BandwidthOrder'] = bandwidth_data['Bandwidth'].apply(
            lambda x: bandwidth_order.index(str(x)) if str(x) in bandwidth_order else 999
        )
        bandwidth_data = bandwidth_data.sort_values('BandwidthOrder')
        
        bw_grouped = bandwidth_data.groupby(['Protocol', 'Bandwidth'])['Throughput(KB/s)'].mean().reset_index()
        
        for protocol in ['HTTP/2.0', 'HTTP/3.0']:
            protocol_data = bw_grouped[bw_grouped['Protocol'] == protocol]
            if not protocol_data.empty:
                axes[1].plot(range(len(protocol_data)), protocol_data['Throughput(KB/s)'], 
                            marker='o', label=protocol, linewidth=2)
        
        if not bw_grouped.empty:
            unique_bw = bw_grouped['Bandwidth'].unique()
            axes[1].set_xticks(range(len(unique_bw)))
            axes[1].set_xticklabels(unique_bw, rotation=45)
        
        axes[1].set_xlabel('Bandwidth Limit', fontsize=12)
        axes[1].set_ylabel('Average Throughput (KB/s)', fontsize=12)
        axes[1].set_title('Throughput vs Bandwidth (No Delay)', fontsize=14, fontweight='bold')
    else:
        # 帯域幅が1種類のみの場合: 遅延による詳細グラフ（エラーバー付き）
        delay_detail = df.groupby(['Protocol', 'NetworkDelay(ms)'])['Throughput(KB/s)'].agg(['mean', 'std']).reset_index()
        
        for protocol in ['HTTP/2.0', 'HTTP/3.0']:
            protocol_data = delay_detail[delay_detail['Protocol'] == protocol]
            if not protocol_data.empty:
                axes[1].errorbar(protocol_data['NetworkDelay(ms)'], protocol_data['mean'], 
                               yerr=protocol_data['std'], marker='o', label=protocol, 
                               linewidth=2, capsize=5, alpha=0.7)
        
        axes[1].set_xlabel('Network Delay (ms)', fontsize=12)
        axes[1].set_ylabel('Average Throughput (KB/s)', fontsize=12)
        axes[1].set_title(f'Throughput with Error Bars ({unique_bandwidths[0]} bandwidth)', fontsize=14, fontweight='bold')
    
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
        if not protocol_data.empty:
            pivot = protocol_data.pivot_table(
                values='TTFB(ms)', 
                index='NetworkDelay(ms)', 
                columns='Bandwidth', 
                aggfunc='mean'
            )
            
            sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd', ax=axes[idx], 
                       cbar_kws={'label': 'TTFB (ms)'})
            axes[idx].set_title(f'{protocol} - TTFB Heatmap', fontsize=14, fontweight='bold')
            axes[idx].set_xlabel('Bandwidth Limit', fontsize=12)
            axes[idx].set_ylabel('Network Delay (ms)', fontsize=12)
        else:
            axes[idx].text(0.5, 0.5, f'No data for {protocol}', 
                          ha='center', va='center', fontsize=14)
    
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
            f.write(f"Bandwidth: {row['Bandwidth']}\n")
            f.write(f"  TTFB: {row[('TTFB(ms)', 'mean')]:.3f} ± {row[('TTFB(ms)', 'std')]:.3f} ms\n")
            f.write(f"  Total Time: {row[('TotalTime(ms)', 'mean')]:.3f} ± {row[('TotalTime(ms)', 'std')]:.3f} ms\n")
            f.write(f"  Throughput: {row[('Throughput(KB/s)', 'mean')]:.2f} ± {row[('Throughput(KB/s)', 'std')]:.2f} KB/s\n")
        
        # 勝者判定
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("Winner Analysis:\n")
        f.write("=" * 80 + "\n")
        
        for delay in sorted(df['NetworkDelay(ms)'].unique()):
            for bandwidth in df['Bandwidth'].unique():
                condition_data = df[(df['NetworkDelay(ms)'] == delay) & (df['Bandwidth'] == bandwidth)]
                if len(condition_data) == 0:
                    continue
                
                http2_ttfb = condition_data[condition_data['Protocol'] == 'HTTP/2.0']['TTFB(ms)'].mean()
                http3_ttfb = condition_data[condition_data['Protocol'] == 'HTTP/3.0']['TTFB(ms)'].mean()
                
                if pd.isna(http2_ttfb) or pd.isna(http3_ttfb):
                    continue
                
                winner = 'HTTP/2.0' if http2_ttfb < http3_ttfb else 'HTTP/3.0'
                diff_pct = abs(http2_ttfb - http3_ttfb) / min(http2_ttfb, http3_ttfb) * 100
                
                f.write(f"\nDelay: {delay}ms, Bandwidth: {bandwidth}\n")
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
    print(f"Network conditions: {len(df.groupby(['NetworkDelay(ms)', 'Bandwidth']))} patterns")
    
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

