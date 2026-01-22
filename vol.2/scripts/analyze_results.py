#!/usr/bin/env python3
"""
ベンチマーク結果を分析して比較グラフを生成するスクリプト
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 非表示バックエンド
import matplotlib.pyplot as plt
import numpy as np
import glob
import os
import sys
from pathlib import Path

# 日本語フォント設定
# Dockerコンテナ内で利用可能なフォントを優先的に使用
import matplotlib.font_manager as fm

# 利用可能な日本語フォントを検索
try:
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    japanese_fonts = []
    
    # Notoフォントを優先的に検索
    preferred_fonts = ['Noto Sans CJK JP', 'Noto Sans CJK', 'Noto Sans', 'DejaVu Sans']
    for font_name in preferred_fonts:
        if font_name in available_fonts:
            japanese_fonts.append(font_name)
            break
    
    # フォントが見つからない場合はデフォルトを使用
    if not japanese_fonts:
        japanese_fonts = ['DejaVu Sans']
    
    plt.rcParams['font.sans-serif'] = japanese_fonts
except Exception as e:
    # エラーが発生した場合はデフォルトフォントを使用
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    print(f"Warning: Font configuration failed: {e}")

plt.rcParams['axes.unicode_minus'] = False

# カラースキーム定義
COLORS = {
    'http2': {
        'main': '#2C5F8D',      # 濃い青
        'fill': '#4A90E2',      # ライトブルー（塗りつぶし）
        'marker': '#1E88E5',    # マーカー色
        'edge': '#2C5F8D',      # マーカーエッジ
    },
    'http3': {
        'main': '#2E86AB',      # 濃い青（HTTP/3用）
        'fill': '#6BB6FF',      # ライトブルー（塗りつぶし）
        'marker': '#2E86AB',    # マーカー色
        'edge': '#1A5F7A',      # マーカーエッジ
    },
    'grid': '#CCCCCC',          # グリッド色
    'zeroline': '#E74C3C',      # ゼロライン色
    'axis': '#34495E',          # 軸の色
    'text': '#2C3E50',          # テキスト色
    'label_bg': '#ECF0F1',      # ラベル背景
    'label_edge': '#3498DB',    # ラベル枠線
}

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

def plot_single_graph(ax, x_data, y_data_dict, x_label, y_label, title, protocol_colors, show_labels=True, fill_area=True, label_unit='ms'):
    """単一グラフを描画するヘルパー関数（デザイン仕様準拠）"""
    # 背景色設定
    ax.set_facecolor('white')
    
    # グリッド設定
    ax.grid(True, alpha=0.4, linestyle='--', linewidth=0.8, color=COLORS['grid'], zorder=0)
    ax.set_axisbelow(True)
    
    # ゼロライン
    y_min = min([min(v) for v in y_data_dict.values() if len(v) > 0]) if y_data_dict else 0
    y_max = max([max(v) for v in y_data_dict.values() if len(v) > 0]) if y_data_dict else 1
    if y_min <= 0 <= y_max:
        ax.axhline(y=0, color=COLORS['zeroline'], linestyle='--', linewidth=2, alpha=0.7, zorder=1)
    
    # 各プロトコルのデータをプロット
    for protocol, y_values in y_data_dict.items():
        if len(x_data) == 0 or len(y_values) == 0:
            continue
            
        color_key = 'http2' if 'HTTP/2' in protocol else 'http3'
        colors = protocol_colors[color_key]
        
        # 滑らかな曲線用の補間
        if len(x_data) > 1:
            x_smooth = np.linspace(x_data.min(), x_data.max(), 300)
            y_smooth = np.interp(x_smooth, x_data, y_values)
            
            # 塗りつぶし（オプション）
            if fill_area:
                ax.fill_between(x_smooth, 0, y_smooth, alpha=0.3, color=colors['fill'], zorder=2)
            
            # 曲線
            ax.plot(x_smooth, y_smooth, color=colors['main'], linewidth=3, alpha=0.95, zorder=3, label=protocol)
        
        # マーカー（データポイント）
        ax.scatter(x_data, y_values, s=200, c=colors['marker'], marker='o', 
                  edgecolors=colors['edge'], linewidths=2.5, alpha=0.95, zorder=5)
        
        # データラベル
        if show_labels and len(x_data) > 0:
            y_range = y_max - y_min if y_max > y_min else 1
            offset = y_range * 0.08
            
            for x_val, y_val in zip(x_data, y_values):
                # ラベル位置を自動調整（上下）
                label_y = y_val + offset if y_val < (y_min + y_max) / 2 else y_val - offset
                
                # ラベルフォーマット
                if label_unit == 'ms':
                    label_text = f'{y_val:.1f}ms'
                elif label_unit == 'KB/s':
                    label_text = f'{y_val:.0f}KB/s'
                else:
                    label_text = f'{y_val:.1f}'
                
                ax.annotate(label_text, 
                           xy=(x_val, y_val), 
                           xytext=(x_val, label_y),
                           fontsize=11, fontweight='bold', color=COLORS['text'],
                           ha='center', va='bottom' if label_y > y_val else 'top',
                           bbox=dict(boxstyle='round,pad=0.6', 
                                    facecolor=COLORS['label_bg'], 
                                    edgecolor=COLORS['label_edge'], 
                                    linewidth=1.5, alpha=0.95),
                           arrowprops=dict(arrowstyle='->', color=COLORS['label_edge'], 
                                         lw=1.5, alpha=0.8),
                           zorder=6)
    
    # 軸の設定
    ax.set_xlabel(x_label, fontsize=16, fontweight='bold', color=COLORS['axis'], labelpad=15)
    ax.set_ylabel(y_label, fontsize=16, fontweight='bold', color=COLORS['axis'], labelpad=15)
    ax.set_title(title, fontsize=18, fontweight='bold', color=COLORS['text'], pad=20)
    
    # 目盛り設定
    ax.tick_params(axis='both', which='major', labelsize=14, width=1.5, 
                   length=6, color=COLORS['axis'], labelcolor=COLORS['axis'])
    
    # 軸の枠線
    for spine in ax.spines.values():
        spine.set_linewidth(2)
        spine.set_color(COLORS['axis'])
    
    # 凡例
    ax.legend(loc='upper left', fontsize=12, framealpha=0.95, 
             edgecolor=COLORS['axis'], frameon=True)
    
    # Y軸範囲の調整（上下12%の余白）
    if y_data_dict:
        all_values = [v for values in y_data_dict.values() for v in values if len(values) > 0]
        if all_values:
            y_min_val = min(all_values)
            y_max_val = max(all_values)
            y_range = y_max_val - y_min_val if y_max_val > y_min_val else 1
            ax.set_ylim(y_min_val - y_range * 0.12, y_max_val + y_range * 0.12)

def plot_ttfb_comparison(df, output_dir):
    """TTFBの比較グラフ（デザイン仕様準拠）"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 8))
    fig.patch.set_facecolor('white')
    
    # データの特性を検出
    unique_bandwidths = df['Bandwidth'].unique()
    unique_delays = df['NetworkDelay(ms)'].unique()
    
    # 左側のグラフ: 遅延による影響
    if len(unique_bandwidths) > 1:
        delay_data = df[(df['Bandwidth'] == '0') | (df['Bandwidth'] == 0)].groupby(['Protocol', 'NetworkDelay(ms)'])['TTFB(ms)'].mean().reset_index()
        bandwidth_label = "帯域無制限"
    else:
        delay_data = df.groupby(['Protocol', 'NetworkDelay(ms)'])['TTFB(ms)'].mean().reset_index()
        bandwidth_label = f"帯域幅: {unique_bandwidths[0]}"
    
    # データを整理
    y_data_dict = {}
    x_data = None
    
    for protocol in ['HTTP/2.0', 'HTTP/3.0']:
        protocol_data = delay_data[delay_data['Protocol'] == protocol].sort_values('NetworkDelay(ms)')
        if not protocol_data.empty:
            if x_data is None:
                x_data = protocol_data['NetworkDelay(ms)'].values
            y_data_dict[protocol] = protocol_data['TTFB(ms)'].values
    
    if x_data is not None and len(y_data_dict) > 0:
        plot_single_graph(axes[0], x_data, y_data_dict, 
                         'ネットワーク遅延 (ms)', '平均TTFB (ms)', 
                         f'TTFB vs ネットワーク遅延 ({bandwidth_label})',
                         COLORS, show_labels=True, fill_area=True, label_unit='ms')
    
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
        # BandwidthOrderを追加
        bw_grouped['BandwidthOrder'] = bw_grouped['Bandwidth'].apply(
            lambda x: bandwidth_order.index(str(x)) if str(x) in bandwidth_order else 999
        )
        bw_grouped = bw_grouped.sort_values('BandwidthOrder')
        
        y_data_dict = {}
        x_indices = None
        
        for protocol in ['HTTP/2.0', 'HTTP/3.0']:
            protocol_data = bw_grouped[bw_grouped['Protocol'] == protocol].sort_values('BandwidthOrder')
            if not protocol_data.empty:
                if x_indices is None:
                    unique_bw = protocol_data['Bandwidth'].unique()
                    x_indices = np.arange(len(unique_bw))
                y_data_dict[protocol] = protocol_data['TTFB(ms)'].values
        
        if x_indices is not None and len(y_data_dict) > 0:
            axes[1].set_facecolor('white')
            axes[1].grid(True, alpha=0.4, linestyle='--', linewidth=0.8, color=COLORS['grid'], zorder=0)
            axes[1].set_axisbelow(True)
            
            for protocol, y_values in y_data_dict.items():
                color_key = 'http2' if 'HTTP/2' in protocol else 'http3'
                colors = COLORS[color_key]
                
                axes[1].plot(x_indices, y_values, color=colors['main'], linewidth=3, 
                           alpha=0.95, marker='o', markersize=10, label=protocol, zorder=3)
                axes[1].scatter(x_indices, y_values, s=200, c=colors['marker'], marker='o', 
                              edgecolors=colors['edge'], linewidths=2.5, alpha=0.95, zorder=5)
            
            unique_bw = bw_grouped['Bandwidth'].unique()
            axes[1].set_xticks(x_indices)
            axes[1].set_xticklabels(unique_bw, rotation=45, ha='right')
            axes[1].set_xlabel('帯域幅制限', fontsize=16, fontweight='bold', color=COLORS['axis'], labelpad=15)
            axes[1].set_ylabel('平均TTFB (ms)', fontsize=16, fontweight='bold', color=COLORS['axis'], labelpad=15)
            axes[1].set_title('TTFB vs 帯域幅 (遅延なし)', fontsize=18, fontweight='bold', color=COLORS['text'], pad=20)
            axes[1].legend(loc='upper left', fontsize=12, framealpha=0.95, edgecolor=COLORS['axis'])
            axes[1].tick_params(axis='both', which='major', labelsize=14, width=1.5, length=6, color=COLORS['axis'])
            for spine in axes[1].spines.values():
                spine.set_linewidth(2)
                spine.set_color(COLORS['axis'])
    else:
        # 帯域幅が1種類のみの場合: 遅延による詳細グラフ
        delay_detail = df.groupby(['Protocol', 'NetworkDelay(ms)'])['TTFB(ms)'].agg(['mean', 'std']).reset_index()
        
        y_data_dict = {}
        y_err_dict = {}
        x_data = None
        
        for protocol in ['HTTP/2.0', 'HTTP/3.0']:
            protocol_data = delay_detail[delay_detail['Protocol'] == protocol].sort_values('NetworkDelay(ms)')
            if not protocol_data.empty:
                if x_data is None:
                    x_data = protocol_data['NetworkDelay(ms)'].values
                y_data_dict[protocol] = protocol_data['mean'].values
                y_err_dict[protocol] = protocol_data['std'].values
        
        if x_data is not None and len(y_data_dict) > 0:
            axes[1].set_facecolor('white')
            axes[1].grid(True, alpha=0.4, linestyle='--', linewidth=0.8, color=COLORS['grid'], zorder=0)
            axes[1].set_axisbelow(True)
            
            for protocol, y_values in y_data_dict.items():
                color_key = 'http2' if 'HTTP/2' in protocol else 'http3'
                colors = COLORS[color_key]
                y_err = y_err_dict.get(protocol, np.zeros_like(y_values))
                
                axes[1].errorbar(x_data, y_values, yerr=y_err, color=colors['main'], 
                               linewidth=3, alpha=0.95, marker='o', markersize=10, 
                               capsize=5, label=protocol, zorder=3)
                axes[1].scatter(x_data, y_values, s=200, c=colors['marker'], marker='o', 
                              edgecolors=colors['edge'], linewidths=2.5, alpha=0.95, zorder=5)
            
            axes[1].set_xlabel('ネットワーク遅延 (ms)', fontsize=16, fontweight='bold', color=COLORS['axis'], labelpad=15)
            axes[1].set_ylabel('平均TTFB (ms)', fontsize=16, fontweight='bold', color=COLORS['axis'], labelpad=15)
            axes[1].set_title(f'TTFB（エラーバー付き） ({unique_bandwidths[0]} 帯域幅)', 
                            fontsize=18, fontweight='bold', color=COLORS['text'], pad=20)
            axes[1].legend(loc='upper left', fontsize=12, framealpha=0.95, edgecolor=COLORS['axis'])
            axes[1].tick_params(axis='both', which='major', labelsize=14, width=1.5, length=6, color=COLORS['axis'])
            for spine in axes[1].spines.values():
                spine.set_linewidth(2)
                spine.set_color(COLORS['axis'])
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'ttfb_comparison.png'), dpi=300, 
                bbox_inches='tight', facecolor='white', pad_inches=0.2)
    print(f"Saved: {output_dir}/ttfb_comparison.png")
    plt.close()

def plot_throughput_comparison(df, output_dir):
    """スループットの比較グラフ（デザイン仕様準拠）"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 8))
    fig.patch.set_facecolor('white')
    
    # データの特性を検出
    unique_bandwidths = df['Bandwidth'].unique()
    unique_delays = df['NetworkDelay(ms)'].unique()
    
    # 左側のグラフ: 遅延による影響
    if len(unique_bandwidths) > 1:
        delay_data = df[(df['Bandwidth'] == '0') | (df['Bandwidth'] == 0)].groupby(['Protocol', 'NetworkDelay(ms)'])['Throughput(KB/s)'].mean().reset_index()
        bandwidth_label = "帯域無制限"
    else:
        delay_data = df.groupby(['Protocol', 'NetworkDelay(ms)'])['Throughput(KB/s)'].mean().reset_index()
        bandwidth_label = f"帯域幅: {unique_bandwidths[0]}"
    
    # データを整理
    y_data_dict = {}
    x_data = None
    
    for protocol in ['HTTP/2.0', 'HTTP/3.0']:
        protocol_data = delay_data[delay_data['Protocol'] == protocol].sort_values('NetworkDelay(ms)')
        if not protocol_data.empty:
            if x_data is None:
                x_data = protocol_data['NetworkDelay(ms)'].values
            y_data_dict[protocol] = protocol_data['Throughput(KB/s)'].values
    
    if x_data is not None and len(y_data_dict) > 0:
        plot_single_graph(axes[0], x_data, y_data_dict, 
                         'ネットワーク遅延 (ms)', '平均スループット (KB/s)', 
                         f'スループット vs ネットワーク遅延 ({bandwidth_label})',
                         COLORS, show_labels=True, fill_area=False, label_unit='KB/s')
    
    # 右側のグラフ: 帯域幅または遅延による影響
    if len(unique_bandwidths) > 1:
        # 帯域幅が複数ある場合: 帯域幅による影響（遅延0msの場合）
        bandwidth_data = df[df['NetworkDelay(ms)'] == 0].copy()
        bandwidth_order = ['100mbit', '10mbit', '5mbit', '1mbit', '0']
        bandwidth_data['BandwidthOrder'] = bandwidth_data['Bandwidth'].apply(
            lambda x: bandwidth_order.index(str(x)) if str(x) in bandwidth_order else 999
        )
        bandwidth_data = bandwidth_data.sort_values('BandwidthOrder')
        
        bw_grouped = bandwidth_data.groupby(['Protocol', 'Bandwidth'])['Throughput(KB/s)'].mean().reset_index()
        # BandwidthOrderを追加
        bw_grouped['BandwidthOrder'] = bw_grouped['Bandwidth'].apply(
            lambda x: bandwidth_order.index(str(x)) if str(x) in bandwidth_order else 999
        )
        bw_grouped = bw_grouped.sort_values('BandwidthOrder')
        
        y_data_dict = {}
        x_indices = None
        
        for protocol in ['HTTP/2.0', 'HTTP/3.0']:
            protocol_data = bw_grouped[bw_grouped['Protocol'] == protocol].sort_values('BandwidthOrder')
            if not protocol_data.empty:
                if x_indices is None:
                    unique_bw = protocol_data['Bandwidth'].unique()
                    x_indices = np.arange(len(unique_bw))
                y_data_dict[protocol] = protocol_data['Throughput(KB/s)'].values
        
        if x_indices is not None and len(y_data_dict) > 0:
            axes[1].set_facecolor('white')
            axes[1].grid(True, alpha=0.4, linestyle='--', linewidth=0.8, color=COLORS['grid'], zorder=0)
            axes[1].set_axisbelow(True)
            
            for protocol, y_values in y_data_dict.items():
                color_key = 'http2' if 'HTTP/2' in protocol else 'http3'
                colors = COLORS[color_key]
                
                axes[1].plot(x_indices, y_values, color=colors['main'], linewidth=3, 
                           alpha=0.95, marker='o', markersize=10, label=protocol, zorder=3)
                axes[1].scatter(x_indices, y_values, s=200, c=colors['marker'], marker='o', 
                              edgecolors=colors['edge'], linewidths=2.5, alpha=0.95, zorder=5)
            
            unique_bw = bw_grouped['Bandwidth'].unique()
            axes[1].set_xticks(x_indices)
            axes[1].set_xticklabels(unique_bw, rotation=45, ha='right')
            axes[1].set_xlabel('帯域幅制限', fontsize=16, fontweight='bold', color=COLORS['axis'], labelpad=15)
            axes[1].set_ylabel('平均スループット (KB/s)', fontsize=16, fontweight='bold', color=COLORS['axis'], labelpad=15)
            axes[1].set_title('スループット vs 帯域幅 (遅延なし)', fontsize=18, fontweight='bold', color=COLORS['text'], pad=20)
            axes[1].legend(loc='upper left', fontsize=12, framealpha=0.95, edgecolor=COLORS['axis'])
            axes[1].tick_params(axis='both', which='major', labelsize=14, width=1.5, length=6, color=COLORS['axis'])
            for spine in axes[1].spines.values():
                spine.set_linewidth(2)
                spine.set_color(COLORS['axis'])
    else:
        # 帯域幅が1種類のみの場合: 遅延による詳細グラフ（エラーバー付き）
        delay_detail = df.groupby(['Protocol', 'NetworkDelay(ms)'])['Throughput(KB/s)'].agg(['mean', 'std']).reset_index()
        
        y_data_dict = {}
        y_err_dict = {}
        x_data = None
        
        for protocol in ['HTTP/2.0', 'HTTP/3.0']:
            protocol_data = delay_detail[delay_detail['Protocol'] == protocol].sort_values('NetworkDelay(ms)')
            if not protocol_data.empty:
                if x_data is None:
                    x_data = protocol_data['NetworkDelay(ms)'].values
                y_data_dict[protocol] = protocol_data['mean'].values
                y_err_dict[protocol] = protocol_data['std'].values
        
        if x_data is not None and len(y_data_dict) > 0:
            axes[1].set_facecolor('white')
            axes[1].grid(True, alpha=0.4, linestyle='--', linewidth=0.8, color=COLORS['grid'], zorder=0)
            axes[1].set_axisbelow(True)
            
            for protocol, y_values in y_data_dict.items():
                color_key = 'http2' if 'HTTP/2' in protocol else 'http3'
                colors = COLORS[color_key]
                y_err = y_err_dict.get(protocol, np.zeros_like(y_values))
                
                axes[1].errorbar(x_data, y_values, yerr=y_err, color=colors['main'], 
                               linewidth=3, alpha=0.95, marker='o', markersize=10, 
                               capsize=5, label=protocol, zorder=3)
                axes[1].scatter(x_data, y_values, s=200, c=colors['marker'], marker='o', 
                              edgecolors=colors['edge'], linewidths=2.5, alpha=0.95, zorder=5)
            
            axes[1].set_xlabel('ネットワーク遅延 (ms)', fontsize=16, fontweight='bold', color=COLORS['axis'], labelpad=15)
            axes[1].set_ylabel('平均スループット (KB/s)', fontsize=16, fontweight='bold', color=COLORS['axis'], labelpad=15)
            axes[1].set_title(f'スループット（エラーバー付き） ({unique_bandwidths[0]} 帯域幅)', 
                            fontsize=18, fontweight='bold', color=COLORS['text'], pad=20)
            axes[1].legend(loc='upper left', fontsize=12, framealpha=0.95, edgecolor=COLORS['axis'])
            axes[1].tick_params(axis='both', which='major', labelsize=14, width=1.5, length=6, color=COLORS['axis'])
            for spine in axes[1].spines.values():
                spine.set_linewidth(2)
                spine.set_color(COLORS['axis'])
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'throughput_comparison.png'), dpi=300, 
                bbox_inches='tight', facecolor='white', pad_inches=0.2)
    print(f"Saved: {output_dir}/throughput_comparison.png")
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
    try:
        if len(sys.argv) < 2:
            print("Usage: python analyze_results.py <results_directory>")
            sys.exit(1)
        
        results_dir = sys.argv[1]
        
        if not os.path.exists(results_dir):
            print(f"Error: Directory '{results_dir}' does not exist")
            print(f"Current directory: {os.getcwd()}")
            print(f"Looking for: {os.path.abspath(results_dir)}")
            sys.exit(1)
        
        print("Loading benchmark results...")
        df = load_results(results_dir)
        
        if df is None or len(df) == 0:
            print("No data to analyze")
            print(f"Checked directory: {results_dir}")
            sys.exit(1)
        
        print(f"Loaded {len(df)} records")
        print(f"Protocols: {df['Protocol'].unique()}")
        print(f"Network conditions: {len(df.groupby(['NetworkDelay(ms)', 'Bandwidth']))} patterns")
        
        # グラフ出力ディレクトリ
        output_dir = os.path.join(results_dir, 'analysis')
        print(f"\nCreating output directory: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        
        # ディレクトリが作成されたか確認
        if not os.path.exists(output_dir):
            print(f"Error: Failed to create directory: {output_dir}")
            sys.exit(1)
        
        print("\nGenerating analysis...")
        try:
            plot_ttfb_comparison(df, output_dir)
        except Exception as e:
            print(f"Warning: Failed to generate TTFB comparison: {e}")
        
        try:
            plot_throughput_comparison(df, output_dir)
        except Exception as e:
            print(f"Warning: Failed to generate throughput comparison: {e}")
        
        try:
            generate_summary_report(df, output_dir)
        except Exception as e:
            print(f"Warning: Failed to generate summary report: {e}")
        
        print("\n" + "=" * 80)
        print("Analysis completed!")
        print(f"Results saved to: {output_dir}")
        
        # 生成されたファイルを確認
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            if files:
                print(f"Generated files: {', '.join(files)}")
            else:
                print("Warning: No files were generated")
        
        print("=" * 80)
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ ERROR: Analysis failed!")
        print("=" * 80)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"\nCurrent directory: {os.getcwd()}")
        if len(sys.argv) >= 2:
            print(f"Target directory: {sys.argv[1]}")
        print("\nTroubleshooting:")
        print("  1. Check if the directory exists and contains CSV files")
        print("  2. Ensure you have write permissions")
        print("  3. Verify Python packages are installed:")
        print("     pip3 install matplotlib pandas seaborn")
        print("  4. Check available disk space")
        print("\nFull error traceback:")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

