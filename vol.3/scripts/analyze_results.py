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
from scipy.interpolate import make_interp_spline
from scipy.signal import savgol_filter

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
# 全体のデフォルトフォントを少し大きめにする
plt.rcParams['font.size'] = 15

# カラースキーム定義（画像デザイン準拠）
COLORS = {
    'http2': {
        'main': '#2E86AB',      # 濃い青（メインカーブ）
        'fill': '#4A90E2',      # ライトブルー（標準偏差塗りつぶし、alpha=0.25-0.3）
        'marker': '#2E86AB',    # マーカー色（明るい青）
        'edge': '#1E88E5',      # マーカーエッジ（白または濃い青）
    },
    'http3': {
        'main': '#A23B72',      # マゼンタ系（メインカーブ）
        'fill': '#FF6B9D',      # ピンク（標準偏差塗りつぶし、alpha=0.2）
        'marker': '#A23B72',    # マーカー色（マゼンタ系）
        'edge': '#C0392B',      # マーカーエッジ（濃い赤）
    },
    'grid': '#CCCCCC',          # グリッド色（alpha=0.3-0.4）
    'zeroline': '#E74C3C',      # ゼロライン色（破線）
    'axis': '#34495E',          # 軸の色（濃いグレー）
    'text': '#2C3E50',          # テキスト色（濃いグレー）
    'label_bg': '#ECF0F1',      # ラベル背景（ライトグレー）
    'label_edge': '#3498DB',    # ラベル枠線（青）
    'background': '#FFFFFF',     # 背景色（白）
}

def load_results(results_dir):
    """結果ファイルを読み込む（新しいディレクトリ構造対応）"""
    # 新しい構造: session_XXX/◯MBps/Experiment/◯ms/http2_results.csv
    # または: session_XXX/◯MBps/Experiment/◯ms/http3_results.csv
    http2_files = []
    http3_files = []
    
    # 再帰的に検索
    for root, dirs, files in os.walk(results_dir):
        if 'http2_results.csv' in files:
            http2_files.append(os.path.join(root, 'http2_results.csv'))
        if 'http3_results.csv' in files:
            http3_files.append(os.path.join(root, 'http3_results.csv'))
    
    # 旧構造も探す: session_XXX/experiment_name/http2_results.csv
    if not http2_files:
        http2_files = glob.glob(os.path.join(results_dir, '*/http2_results.csv'))
    if not http3_files:
        http3_files = glob.glob(os.path.join(results_dir, '*/http3_results.csv'))
    
    # さらに旧構造: http2_*.csv
    if not http2_files:
        http2_files = glob.glob(os.path.join(results_dir, 'http2_*.csv'))
    if not http3_files:
        http3_files = glob.glob(os.path.join(results_dir, 'http3_*.csv'))
    
    dfs = []
    for file in http2_files + http3_files:
        try:
            df = pd.read_csv(file)
            # パスから帯域幅と遅延を抽出
            path_parts = file.replace(results_dir, '').split(os.sep)
            path_parts = [p for p in path_parts if p]
            
            # 帯域幅ディレクトリ名を取得
            for part in path_parts:
                if 'Mbps' in part or part == '無制限':
                    df['BandwidthDir'] = part
                    break
            
            # 遅延ディレクトリ名を取得
            for part in path_parts:
                if 'ms' in part:
                    delay_str = part.replace('ms', '')
                    try:
                        df['ExtractedDelay'] = int(delay_str)
                    except:
                        pass
                    break
            
            dfs.append(df)
        except Exception as e:
            print(f"Warning: Failed to load {file}: {e}")
    
    if not dfs:
        print("No result files found!")
        return None
    
    result_df = pd.concat(dfs, ignore_index=True)
    
    # 帯域幅ディレクトリ名からBandwidth値を補完（必要に応じて）
    if 'BandwidthDir' in result_df.columns:
        bandwidth_mapping = {
            '無制限': '0',
            '1Mbps': '1mbit',
            '2Mbps': '2mbit',
            '3Mbps': '3mbit'
        }
        for idx, row in result_df.iterrows():
            if pd.isna(row.get('Bandwidth')) or row.get('Bandwidth') == '':
                bw_dir = row.get('BandwidthDir', '')
                if bw_dir in bandwidth_mapping:
                    result_df.at[idx, 'Bandwidth'] = bandwidth_mapping[bw_dir]
    
    # 抽出した遅延値で補完（必要に応じて）
    if 'ExtractedDelay' in result_df.columns:
        for idx, row in result_df.iterrows():
            if pd.isna(row.get('NetworkDelay(ms)')):
                extracted = row.get('ExtractedDelay')
                if not pd.isna(extracted):
                    result_df.at[idx, 'NetworkDelay(ms)'] = extracted
    
    return result_df

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

def plot_single_graph(ax, x_data, y_data_dict, x_label, y_label, title, protocol_colors, show_labels=True, fill_area=True, label_unit='ms', y_std_dict=None):
    """単一グラフを描画するヘルパー関数（画像デザイン完全再現・スムージング版）"""
    # 背景色設定
    ax.set_facecolor(COLORS['background'])
    
    # グリッド設定（画像準拠：破線、グレー、alpha=0.3-0.4）
    ax.grid(True, alpha=0.35, linestyle='--', linewidth=0.8, color=COLORS['grid'], zorder=0)
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
        
        # HTTP/3は破線、HTTP/2は実線
        linestyle = '--' if 'HTTP/3' in protocol else '-'
        # HTTP/3は四角形マーカー、HTTP/2は円形マーカー
        marker_shape = 's' if 'HTTP/3' in protocol else 'o'
        
        # 標準偏差の取得
        y_std = None
        if y_std_dict and protocol in y_std_dict:
            y_std = y_std_dict[protocol]
        
        # データをnumpy配列に変換
        x_array = np.array(x_data)
        y_array = np.array(y_values)
        
        # NaN値を処理
        valid_mask = ~np.isnan(y_array)
        if not valid_mask.any():
            continue
        
        valid_x = x_array[valid_mask]
        valid_y = y_array[valid_mask]
        valid_std = y_std[valid_mask] if y_std is not None and len(y_std) == len(y_values) else None
        
        # 外れ値に影響されない高品質なスムージング処理
        if len(valid_x) >= 5:  # Savitzky-Golayフィルタには最低5点必要
            # 窓サイズを大きくして滑らかに（最大51）
            window_length = min(51, len(valid_y) if len(valid_y) % 2 == 1 else len(valid_y) - 1)
            if window_length < 5:
                window_length = 5
            polyorder = min(3, window_length - 1)
            
            try:
                # Savitzky-Golayフィルタを適用
                smoothed_y = savgol_filter(valid_y, window_length, polyorder)
                if valid_std is not None:
                    smoothed_std = savgol_filter(valid_std, window_length, polyorder)
                    smoothed_std = np.maximum(smoothed_std, 0)  # 負の値にならないように
                else:
                    smoothed_std = None
            except Exception as e:
                print(f"警告: Savitzky-Golayフィルタに失敗しました ({protocol}): {e}. 元のデータを使用します。")
                smoothed_y = valid_y
                smoothed_std = valid_std
        else:
            smoothed_y = valid_y
            smoothed_std = valid_std
        
        # 3次スプライン補間で極めて滑らかな曲線を作成
        if len(valid_x) >= 4:
            # 補間点を大幅に増やす（100倍）で極めて滑らかな曲線を実現
            num_points = len(valid_x) * 100
            smooth_x = np.linspace(valid_x.min(), valid_x.max(), num_points)
            
            try:
                # 3次スプライン補間
                spl = make_interp_spline(valid_x, smoothed_y, k=3)
                smooth_y = spl(smooth_x)
                
                # 標準偏差も滑らかに補間
                if smoothed_std is not None:
                    smooth_std = np.interp(smooth_x, valid_x, smoothed_std)
                else:
                    smooth_std = None
            except Exception as e:
                # スプライン補間が失敗した場合は線形補間を使用
                print(f"警告: スプライン補間に失敗しました ({protocol}): {e}. 線形補間を使用します。")
                smooth_x = np.linspace(valid_x.min(), valid_x.max(), num_points)
                smooth_y = np.interp(smooth_x, valid_x, smoothed_y)
                if smoothed_std is not None:
                    smooth_std = np.interp(smooth_x, valid_x, smoothed_std)
                else:
                    smooth_std = None
        else:
            smooth_x = valid_x
            smooth_y = smoothed_y
            smooth_std = smoothed_std
        
        # 標準偏差の塗りつぶし（スムージングされた曲線に基づく）
        if smooth_std is not None:
            lower = smooth_y - smooth_std
            upper = smooth_y + smooth_std
            ax.fill_between(smooth_x, lower, upper, alpha=0.2, color=colors['fill'], zorder=1, label='_nolegend_')
        elif fill_area:
            ax.fill_between(smooth_x, 0, smooth_y, alpha=0.2, color=colors['fill'], zorder=1)
        
        # スムージングされた曲線をプロット（より太い線で美しく表示）
        ax.plot(smooth_x, smooth_y, linewidth=4.0, label=protocol, color=colors['main'],
               linestyle=linestyle, zorder=3, antialiased=True)
        
        # 元のデータポイントにマーカーを表示（より控えめに）
        ax.plot(valid_x, smoothed_y, marker=marker_shape, markersize=10, linestyle='None',
               color=colors['marker'], zorder=4, alpha=0.6, markeredgewidth=1.5,
               markeredgecolor='white')
        
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
    
    # 軸の設定（画像準拠：タイトル24pt、軸ラベル16-22pt、目盛り12-16pt）
    ax.set_xlabel(x_label, fontsize=20, fontweight='bold', color=COLORS['axis'], labelpad=18)
    ax.set_ylabel(y_label, fontsize=20, fontweight='bold', color=COLORS['axis'], labelpad=18)
    ax.set_title(title, fontsize=24, fontweight='bold', color=COLORS['text'], pad=25)
    
    # 目盛り設定（画像準拠：12-16pt、線幅1.5pt、長さ6pt）
    ax.tick_params(axis='both', which='major', labelsize=14, width=1.5, 
                   length=6, color=COLORS['axis'], labelcolor=COLORS['axis'])
    
    # 軸の枠線
    for spine in ax.spines.values():
        spine.set_linewidth(2)
        spine.set_color(COLORS['axis'])
    
    # 凡例（画像準拠：右上または適切な位置、フォントサイズ22pt）
    ax.legend(loc='upper left', fontsize=22, framealpha=0.9, 
             edgecolor=COLORS['axis'], frameon=True, fancybox=True, shadow=False)
    
    # 標準偏差の注釈を追加（画像準拠：左下、フォントサイズ18pt）
    if y_std_dict:
        ax.text(0.02, 0.75, '※塗りつぶし部分は標準偏差の範囲を示す', 
               transform=ax.transAxes, fontsize=18, fontweight='bold', verticalalignment='top',
               color=COLORS['text'],
               bbox=dict(boxstyle='round,pad=0.6', facecolor='wheat', alpha=0.5, 
                        edgecolor=COLORS['axis'], linewidth=1.5))
    
    # Y軸範囲の調整（上下12%の余白）
    if y_data_dict:
        all_values = [v for values in y_data_dict.values() for v in values if len(values) > 0]
        if all_values:
            y_min_val = min(all_values)
            y_max_val = max(all_values)
            y_range = y_max_val - y_min_val if y_max_val > y_min_val else 1
            ax.set_ylim(y_min_val - y_range * 0.12, y_max_val + y_range * 0.12)

def plot_ttfb_comparison(df, output_dir):
    """TTFBの比較"""
    # データの特性を検出
    unique_bandwidths = df['Bandwidth'].unique()
    unique_delays = df['NetworkDelay(ms)'].unique()
    
    # 帯域幅が1種類のみの場合は1つのグラフのみ表示
    if len(unique_bandwidths) == 1:
        # 単一グラフ表示
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        fig.patch.set_facecolor(COLORS['background'])
        
        delay_data = df.groupby(['Protocol', 'NetworkDelay(ms)'])['TTFB(ms)'].mean().reset_index()
        bandwidth_label = f"帯域幅: {unique_bandwidths[0]}" if unique_bandwidths[0] != '0' and unique_bandwidths[0] != 0 else "帯域無制限"
        
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
            # 標準偏差を計算
            delay_std = df.groupby(['Protocol', 'NetworkDelay(ms)'])['TTFB(ms)'].std().reset_index()
            y_std_dict = {}
            for protocol in ['HTTP/2.0', 'HTTP/3.0']:
                protocol_std = delay_std[delay_std['Protocol'] == protocol].sort_values('NetworkDelay(ms)')
                if not protocol_std.empty:
                    y_std_dict[protocol] = protocol_std['TTFB(ms)'].values
            
            plot_single_graph(ax, x_data, y_data_dict, 
                             'ネットワーク遅延 (ms)', '平均TTFB (ms)', 
                             'TTFBの比較',
                             COLORS, show_labels=True, fill_area=False, label_unit='ms', y_std_dict=y_std_dict if y_std_dict else None)
    else:
        # 帯域幅が複数ある場合は2つのグラフを表示
        fig, axes = plt.subplots(1, 2, figsize=(14, 9))
        fig.patch.set_facecolor(COLORS['background'])
        
        # 左側のグラフ: 遅延による影響（帯域無制限）
        delay_data = df[(df['Bandwidth'] == '0') | (df['Bandwidth'] == 0)].groupby(['Protocol', 'NetworkDelay(ms)'])['TTFB(ms)'].mean().reset_index()
        
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
            # 標準偏差を計算
            delay_std = df[(df['Bandwidth'] == '0') | (df['Bandwidth'] == 0)].groupby(['Protocol', 'NetworkDelay(ms)'])['TTFB(ms)'].std().reset_index()
            y_std_dict = {}
            for protocol in ['HTTP/2.0', 'HTTP/3.0']:
                protocol_std = delay_std[delay_std['Protocol'] == protocol].sort_values('NetworkDelay(ms)')
                if not protocol_std.empty:
                    y_std_dict[protocol] = protocol_std['TTFB(ms)'].values
            
            plot_single_graph(axes[0], x_data, y_data_dict, 
                             'ネットワーク遅延 (ms)', '平均TTFB (ms)', 
                             'TTFBの比較 (帯域無制限)',
                             COLORS, show_labels=True, fill_area=False, label_unit='ms', y_std_dict=y_std_dict if y_std_dict else None)
        
        # 右側のグラフ: 帯域幅による影響（遅延0msの場合）
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
            axes[1].set_xlabel('帯域幅制限', fontsize=20, fontweight='bold', color=COLORS['axis'], labelpad=18)
            axes[1].set_ylabel('平均TTFB (ms)', fontsize=20, fontweight='bold', color=COLORS['axis'], labelpad=18)
            axes[1].set_title('TTFB vs 帯域幅', fontsize=24, fontweight='bold', color=COLORS['text'], pad=25)
            axes[1].legend(loc='upper left', fontsize=22, framealpha=0.9, edgecolor=COLORS['axis'])
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
    """スループットの比較グラフ（画像デザイン完全再現）"""
    # データの特性を検出
    unique_bandwidths = df['Bandwidth'].unique()
    unique_delays = df['NetworkDelay(ms)'].unique()
    
    # 帯域幅が1種類のみの場合は1つのグラフのみ表示
    if len(unique_bandwidths) == 1:
        # 単一グラフ表示
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        fig.patch.set_facecolor(COLORS['background'])
        
        delay_data = df.groupby(['Protocol', 'NetworkDelay(ms)'])['Throughput(KB/s)'].mean().reset_index()
        
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
            # 標準偏差を計算
            delay_std = df.groupby(['Protocol', 'NetworkDelay(ms)'])['Throughput(KB/s)'].std().reset_index()
            y_std_dict = {}
            for protocol in ['HTTP/2.0', 'HTTP/3.0']:
                protocol_std = delay_std[delay_std['Protocol'] == protocol].sort_values('NetworkDelay(ms)')
                if not protocol_std.empty:
                    y_std_dict[protocol] = protocol_std['Throughput(KB/s)'].values
            
            plot_single_graph(ax, x_data, y_data_dict, 
                             'ネットワーク遅延 (ms)', '平均スループット (KB/s)', 
                             'スループットの比較',
                             COLORS, show_labels=True, fill_area=False, label_unit='KB/s', y_std_dict=y_std_dict if y_std_dict else None)
    else:
        # 帯域幅が複数ある場合は2つのグラフを表示
        fig, axes = plt.subplots(1, 2, figsize=(14, 9))
        fig.patch.set_facecolor(COLORS['background'])
        
        # 左側のグラフ: 遅延による影響（帯域無制限）
        delay_data = df[(df['Bandwidth'] == '0') | (df['Bandwidth'] == 0)].groupby(['Protocol', 'NetworkDelay(ms)'])['Throughput(KB/s)'].mean().reset_index()
        
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
            # 標準偏差を計算
            delay_std = df[(df['Bandwidth'] == '0') | (df['Bandwidth'] == 0)].groupby(['Protocol', 'NetworkDelay(ms)'])['Throughput(KB/s)'].std().reset_index()
            y_std_dict = {}
            for protocol in ['HTTP/2.0', 'HTTP/3.0']:
                protocol_std = delay_std[delay_std['Protocol'] == protocol].sort_values('NetworkDelay(ms)')
                if not protocol_std.empty:
                    y_std_dict[protocol] = protocol_std['Throughput(KB/s)'].values
            
            plot_single_graph(axes[0], x_data, y_data_dict, 
                             'ネットワーク遅延 (ms)', '平均スループット (KB/s)', 
                             'スループットの比較 (帯域無制限)',
                             COLORS, show_labels=True, fill_area=False, label_unit='KB/s', y_std_dict=y_std_dict if y_std_dict else None)
        
        # 右側のグラフ: 帯域幅による影響（遅延0msの場合）
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
            axes[1].set_xlabel('帯域幅制限', fontsize=20, fontweight='bold', color=COLORS['axis'], labelpad=18)
            axes[1].set_ylabel('平均スループット (KB/s)', fontsize=20, fontweight='bold', color=COLORS['axis'], labelpad=18)
            axes[1].set_title('スループット vs 帯域幅', fontsize=24, fontweight='bold', color=COLORS['text'], pad=25)
            axes[1].legend(loc='upper left', fontsize=22, framealpha=0.9, edgecolor=COLORS['axis'])
            axes[1].tick_params(axis='both', which='major', labelsize=14, width=1.5, length=6, color=COLORS['axis'])
            for spine in axes[1].spines.values():
                spine.set_linewidth(2)
                spine.set_color(COLORS['axis'])
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'throughput_comparison.png'), dpi=300, 
                bbox_inches='tight', facecolor='white', pad_inches=0.2)
    print(f"Saved: {output_dir}/throughput_comparison.png")
    plt.close()

def plot_total_time_comparison(df, output_dir):
    """Total Timeの比較グラフ"""
    # データの特性を検出
    unique_bandwidths = df['Bandwidth'].unique()
    unique_delays = df['NetworkDelay(ms)'].unique()
    
    # 帯域幅が1種類のみの場合は1つのグラフのみ表示
    if len(unique_bandwidths) == 1:
        # 単一グラフ表示
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        fig.patch.set_facecolor(COLORS['background'])
        
        delay_data = df.groupby(['Protocol', 'NetworkDelay(ms)'])['TotalTime(ms)'].mean().reset_index()
        bandwidth_label = f"帯域幅: {unique_bandwidths[0]}" if unique_bandwidths[0] != '0' and unique_bandwidths[0] != 0 else "帯域無制限"
        
        # データを整理
        y_data_dict = {}
        x_data = None
        
        for protocol in ['HTTP/2.0', 'HTTP/3.0']:
            protocol_data = delay_data[delay_data['Protocol'] == protocol].sort_values('NetworkDelay(ms)')
            if not protocol_data.empty:
                if x_data is None:
                    x_data = protocol_data['NetworkDelay(ms)'].values
                y_data_dict[protocol] = protocol_data['TotalTime(ms)'].values
        
        if x_data is not None and len(y_data_dict) > 0:
            # 標準偏差を計算
            delay_std = df.groupby(['Protocol', 'NetworkDelay(ms)'])['TotalTime(ms)'].std().reset_index()
            y_std_dict = {}
            for protocol in ['HTTP/2.0', 'HTTP/3.0']:
                protocol_std = delay_std[delay_std['Protocol'] == protocol].sort_values('NetworkDelay(ms)')
                if not protocol_std.empty:
                    y_std_dict[protocol] = protocol_std['TotalTime(ms)'].values
            
            plot_single_graph(ax, x_data, y_data_dict, 
                             'ネットワーク遅延 (ms)', '平均Total Time (ms)', 
                             'Total Timeの比較',
                             COLORS, show_labels=True, fill_area=False, label_unit='ms', y_std_dict=y_std_dict if y_std_dict else None)
    else:
        # 帯域幅が複数ある場合は2つのグラフを表示
        fig, axes = plt.subplots(1, 2, figsize=(14, 9))
        fig.patch.set_facecolor(COLORS['background'])
        
        # 左側のグラフ: 遅延による影響（帯域無制限）
        delay_data = df[(df['Bandwidth'] == '0') | (df['Bandwidth'] == 0)].groupby(['Protocol', 'NetworkDelay(ms)'])['TotalTime(ms)'].mean().reset_index()
        
        # データを整理
        y_data_dict = {}
        x_data = None
        
        for protocol in ['HTTP/2.0', 'HTTP/3.0']:
            protocol_data = delay_data[delay_data['Protocol'] == protocol].sort_values('NetworkDelay(ms)')
            if not protocol_data.empty:
                if x_data is None:
                    x_data = protocol_data['NetworkDelay(ms)'].values
                y_data_dict[protocol] = protocol_data['TotalTime(ms)'].values
        
        if x_data is not None and len(y_data_dict) > 0:
            # 標準偏差を計算
            delay_std = df[(df['Bandwidth'] == '0') | (df['Bandwidth'] == 0)].groupby(['Protocol', 'NetworkDelay(ms)'])['TotalTime(ms)'].std().reset_index()
            y_std_dict = {}
            for protocol in ['HTTP/2.0', 'HTTP/3.0']:
                protocol_std = delay_std[delay_std['Protocol'] == protocol].sort_values('NetworkDelay(ms)')
                if not protocol_std.empty:
                    y_std_dict[protocol] = protocol_std['TotalTime(ms)'].values
            
            plot_single_graph(axes[0], x_data, y_data_dict, 
                             'ネットワーク遅延 (ms)', '平均Total Time (ms)', 
                             'Total Timeの比較 (帯域無制限)',
                             COLORS, show_labels=True, fill_area=False, label_unit='ms', y_std_dict=y_std_dict if y_std_dict else None)
        
        # 右側のグラフ: 帯域幅による影響（遅延0msの場合）
        bandwidth_data = df[df['NetworkDelay(ms)'] == 0].copy()
        bandwidth_order = ['100mbit', '10mbit', '5mbit', '3mbit', '2mbit', '1mbit', '0']
        bandwidth_data['BandwidthOrder'] = bandwidth_data['Bandwidth'].apply(
            lambda x: bandwidth_order.index(str(x)) if str(x) in bandwidth_order else 999
        )
        bandwidth_data = bandwidth_data.sort_values('BandwidthOrder')
        
        bw_grouped = bandwidth_data.groupby(['Protocol', 'Bandwidth'])['TotalTime(ms)'].mean().reset_index()
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
                y_data_dict[protocol] = protocol_data['TotalTime(ms)'].values
        
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
            axes[1].set_xlabel('帯域幅制限', fontsize=20, fontweight='bold', color=COLORS['axis'], labelpad=18)
            axes[1].set_ylabel('平均Total Time (ms)', fontsize=20, fontweight='bold', color=COLORS['axis'], labelpad=18)
            axes[1].set_title('Total Time vs 帯域幅', fontsize=24, fontweight='bold', color=COLORS['text'], pad=25)
            axes[1].legend(loc='upper left', fontsize=22, framealpha=0.9, edgecolor=COLORS['axis'])
            axes[1].tick_params(axis='both', which='major', labelsize=14, width=1.5, length=6, color=COLORS['axis'])
            for spine in axes[1].spines.values():
                spine.set_linewidth(2)
                spine.set_color(COLORS['axis'])
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'total_time_comparison.png'), dpi=300, 
                bbox_inches='tight', facecolor='white', pad_inches=0.2)
    print(f"Saved: {output_dir}/total_time_comparison.png")
    plt.close()

def find_crossover_points(df, metric='TTFB(ms)'):
    """HTTP2とHTTP3で性能が逆転する地点を特定"""
    crossover_points = []
    
    # 帯域幅ごとに分析
    for bandwidth in sorted(df['Bandwidth'].unique()):
        bw_data = df[df['Bandwidth'] == bandwidth]
        
        # 遅延ごとに平均値を計算
        delays = sorted(bw_data['NetworkDelay(ms)'].unique())
        
        if len(delays) < 2:
            continue
        
        http2_values = []
        http3_values = []
        delay_list = []
        
        for delay in delays:
            delay_data = bw_data[bw_data['NetworkDelay(ms)'] == delay]
            http2_data = delay_data[delay_data['Protocol'] == 'HTTP/2.0']
            http3_data = delay_data[delay_data['Protocol'] == 'HTTP/3.0']
            
            if len(http2_data) > 0 and len(http3_data) > 0:
                http2_mean = http2_data[metric].mean()
                http3_mean = http3_data[metric].mean()
                
                if not pd.isna(http2_mean) and not pd.isna(http3_mean):
                    http2_values.append(http2_mean)
                    http3_values.append(http3_mean)
                    delay_list.append(delay)
        
        if len(http2_values) < 2:
            continue
        
        # 逆転地点を探す
        prev_http2_better = None
        for i in range(len(delay_list)):
            http2_better = http2_values[i] < http3_values[i]
            
            if prev_http2_better is not None and prev_http2_better != http2_better:
                # 逆転が発生
                crossover_delay = delay_list[i]
                if i > 0:
                    prev_delay = delay_list[i-1]
                    # 線形補間でより正確な逆転地点を推定
                    prev_diff = http2_values[i-1] - http3_values[i-1]
                    curr_diff = http2_values[i] - http3_values[i]
                    
                    if prev_diff != curr_diff:
                        # 線形補間で0になる点を計算
                        ratio = abs(prev_diff) / abs(prev_diff - curr_diff) if (prev_diff - curr_diff) != 0 else 0.5
                        estimated_delay = prev_delay + (crossover_delay - prev_delay) * ratio
                    else:
                        estimated_delay = (prev_delay + crossover_delay) / 2
                else:
                    estimated_delay = crossover_delay
                
                crossover_points.append({
                    'bandwidth': bandwidth,
                    'delay': estimated_delay,
                    'metric': metric,
                    'http2_value': http2_values[i],
                    'http3_value': http3_values[i],
                    'direction': 'HTTP/3優位→HTTP/2優位' if prev_http2_better else 'HTTP/2優位→HTTP/3優位'
                })
            
            prev_http2_better = http2_better
    
    return crossover_points

def consolidate_bandwidth_csv(results_dir, bandwidth, output_dir, df=None):
    """帯域幅ごとのCSVファイルを集約してbenchmark_results.csvを作成"""
    bandwidth_name = bandwidth if bandwidth != '0' else '無制限'
    if bandwidth == '0':
        bandwidth_name = '無制限'
    elif bandwidth == '1mbit':
        bandwidth_name = '1Mbps'
    elif bandwidth == '2mbit':
        bandwidth_name = '2Mbps'
    elif bandwidth == '3mbit':
        bandwidth_name = '3Mbps'
    
    all_dataframes = []
    
    # 方法1: DataFrameが提供されている場合はそれを使用
    if df is not None:
        bw_data = df[df['Bandwidth'] == bandwidth]
        if len(bw_data) > 0:
            all_dataframes.append(bw_data)
    
    # 方法2: Experiment/◯ms/からCSVファイルを探す（新しい構造）
    experiment_dir = os.path.join(results_dir, bandwidth_name, 'Experiment')
    if os.path.exists(experiment_dir):
        for delay_dir in sorted(os.listdir(experiment_dir)):
            delay_path = os.path.join(experiment_dir, delay_dir)
            if not os.path.isdir(delay_path):
                continue
            
            http2_file = os.path.join(delay_path, 'http2_results.csv')
            http3_file = os.path.join(delay_path, 'http3_results.csv')
            
            for csv_file in [http2_file, http3_file]:
                if os.path.exists(csv_file):
                    try:
                        csv_df = pd.read_csv(csv_file)
                        # DataFrameから既に読み込んだデータと重複しないようにチェック
                        if df is None or len(csv_df) > 0:
                            all_dataframes.append(csv_df)
                    except Exception as e:
                        print(f"Warning: Failed to read {csv_file}: {e}")
    
    # 方法3: 古い構造（delay_◯ms/）からCSVファイルを探す
    if not all_dataframes:
        # 帯域幅に基づいて古い構造のディレクトリを探す
        for item in os.listdir(results_dir):
            item_path = os.path.join(results_dir, item)
            if not os.path.isdir(item_path) or not item.startswith('delay_'):
                continue
            
            # experiment_info.txtから帯域幅を確認
            exp_info = os.path.join(item_path, 'experiment_info.txt')
            if os.path.exists(exp_info):
                try:
                    with open(exp_info, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 帯域幅が一致するか確認
                        if (bandwidth == '0' and ('Bandwidth Limit: 0' in content or 'Bandwidth Limit: 無' in content)) or \
                           (bandwidth != '0' and f'Bandwidth Limit: {bandwidth}' in content):
                            http2_file = os.path.join(item_path, 'http2_results.csv')
                            http3_file = os.path.join(item_path, 'http3_results.csv')
                            
                            for csv_file in [http2_file, http3_file]:
                                if os.path.exists(csv_file):
                                    try:
                                        csv_df = pd.read_csv(csv_file)
                                        all_dataframes.append(csv_df)
                                    except Exception as e:
                                        print(f"Warning: Failed to read {csv_file}: {e}")
                except Exception as e:
                    print(f"Warning: Failed to read {exp_info}: {e}")
    
    if not all_dataframes:
        print(f"Warning: No CSV files found for {bandwidth_name}")
        return None
    
    # すべてのデータを結合（重複を除去）
    consolidated_df = pd.concat(all_dataframes, ignore_index=True)
    # 重複行を除去（同じRequestTimeとProtocolの組み合わせ）
    if 'RequestTime' in consolidated_df.columns:
        consolidated_df = consolidated_df.drop_duplicates(subset=['Protocol', 'RequestTime'], keep='first')
    
    # benchmark_results.csvとして保存
    output_file = os.path.join(output_dir, 'benchmark_results.csv')
    consolidated_df.to_csv(output_file, index=False)
    print(f"Saved: {output_file} ({len(consolidated_df)} records)")
    
    return consolidated_df

def generate_bandwidth_report(df, bandwidth, output_dir):
    """帯域幅ごとの詳細分析レポートを生成（detailed_analysis_report.txt）"""
    bandwidth_name = bandwidth if bandwidth != '0' else '無制限'
    if bandwidth == '0':
        bandwidth_name = '無制限'
    elif bandwidth == '1mbit':
        bandwidth_name = '1Mbps'
    elif bandwidth == '2mbit':
        bandwidth_name = '2Mbps'
    elif bandwidth == '3mbit':
        bandwidth_name = '3Mbps'
    else:
        bandwidth_name = bandwidth
    
    report_path = os.path.join(output_dir, 'detailed_analysis_report.txt')
    
    bw_data = df[df['Bandwidth'] == bandwidth]
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(f"HTTP/2 vs HTTP/3 Performance Report - {bandwidth_name}\n")
        f.write("=" * 80 + "\n\n")
        
        # 帯域幅別統計
        f.write(f"Bandwidth Condition: {bandwidth_name}\n")
        f.write("-" * 80 + "\n")
        for protocol in ['HTTP/2.0', 'HTTP/3.0']:
            protocol_data = bw_data[bw_data['Protocol'] == protocol]
            if len(protocol_data) > 0:
                f.write(f"\n{protocol}:\n")
                f.write(f"  Total Requests: {len(protocol_data)}\n")
                f.write(f"  TTFB (avg): {protocol_data['TTFB(ms)'].mean():.3f} ms\n")
                f.write(f"  Total Time (avg): {protocol_data['TotalTime(ms)'].mean():.3f} ms\n")
                f.write(f"  Throughput (avg): {protocol_data['Throughput(KB/s)'].mean():.2f} KB/s\n")
        
        # 遅延ごとの勝者判定
        f.write("\n\nPerformance by Delay:\n")
        f.write("-" * 80 + "\n")
        for delay in sorted(bw_data['NetworkDelay(ms)'].unique()):
            delay_data = bw_data[bw_data['NetworkDelay(ms)'] == delay]
            if len(delay_data) == 0:
                continue
            
            http2_data = delay_data[delay_data['Protocol'] == 'HTTP/2.0']
            http3_data = delay_data[delay_data['Protocol'] == 'HTTP/3.0']
            
            if len(http2_data) > 0 and len(http3_data) > 0:
                http2_ttfb = http2_data['TTFB(ms)'].mean()
                http3_ttfb = http3_data['TTFB(ms)'].mean()
                http2_total = http2_data['TotalTime(ms)'].mean()
                http3_total = http3_data['TotalTime(ms)'].mean()
                
                if not pd.isna(http2_ttfb) and not pd.isna(http3_ttfb):
                    winner_ttfb = 'HTTP/2.0' if http2_ttfb < http3_ttfb else 'HTTP/3.0'
                    winner_total = 'HTTP/2.0' if http2_total < http3_total else 'HTTP/3.0'
                    diff_ttfb = abs(http2_ttfb - http3_ttfb) / min(http2_ttfb, http3_ttfb) * 100
                    diff_total = abs(http2_total - http3_total) / min(http2_total, http3_total) * 100
                    
                    f.write(f"\nDelay: {delay}ms\n")
                    f.write(f"  TTFB Winner: {winner_ttfb} (差: {diff_ttfb:.1f}%)\n")
                    f.write(f"    HTTP/2: {http2_ttfb:.3f} ms, HTTP/3: {http3_ttfb:.3f} ms\n")
                    f.write(f"  Total Time Winner: {winner_total} (差: {diff_total:.1f}%)\n")
                    f.write(f"    HTTP/2: {http2_total:.3f} ms, HTTP/3: {http3_total:.3f} ms\n")
        
        # 逆転地点の特定
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("Performance Crossover Points (逆転地点):\n")
        f.write("=" * 80 + "\n")
        
        # TTFBの逆転地点
        ttfb_crossovers = find_crossover_points(bw_data, 'TTFB(ms)')
        if ttfb_crossovers:
            f.write("\nTTFB (Time To First Byte):\n")
            for cp in ttfb_crossovers:
                f.write(f"  {cp['direction']}\n")
                f.write(f"    推定遅延: {cp['delay']:.1f}ms\n")
                f.write(f"    HTTP/2: {cp['http2_value']:.3f} ms\n")
                f.write(f"    HTTP/3: {cp['http3_value']:.3f} ms\n")
        else:
            f.write("\nTTFB: 逆転地点は見つかりませんでした\n")
        
        # Total Timeの逆転地点
        total_crossovers = find_crossover_points(bw_data, 'TotalTime(ms)')
        if total_crossovers:
            f.write("\nTotal Time:\n")
            for cp in total_crossovers:
                f.write(f"  {cp['direction']}\n")
                f.write(f"    推定遅延: {cp['delay']:.1f}ms\n")
                f.write(f"    HTTP/2: {cp['http2_value']:.3f} ms\n")
                f.write(f"    HTTP/3: {cp['http3_value']:.3f} ms\n")
        else:
            f.write("\nTotal Time: 逆転地点は見つかりませんでした\n")
    
    print(f"Saved: {report_path}")

def plot_bandwidth_response_time_comparison(df, bandwidth, output_dir):
    """帯域幅ごとのResponse Time（Total Time）比較グラフを生成"""
    bandwidth_name = bandwidth if bandwidth != '0' else '無制限'
    if bandwidth == '0':
        bandwidth_name = '無制限'
    elif bandwidth == '1mbit':
        bandwidth_name = '1Mbps'
    elif bandwidth == '2mbit':
        bandwidth_name = '2Mbps'
    elif bandwidth == '3mbit':
        bandwidth_name = '3Mbps'
    
    bw_data = df[df['Bandwidth'] == bandwidth]
    
    # Total Timeの比較グラフを生成
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    fig.patch.set_facecolor(COLORS['background'])
    
    delay_data = bw_data.groupby(['Protocol', 'NetworkDelay(ms)'])['TotalTime(ms)'].mean().reset_index()
    
    # データを整理
    y_data_dict = {}
    x_data = None
    
    for protocol in ['HTTP/2.0', 'HTTP/3.0']:
        protocol_data = delay_data[delay_data['Protocol'] == protocol].sort_values('NetworkDelay(ms)')
        if not protocol_data.empty:
            if x_data is None:
                x_data = protocol_data['NetworkDelay(ms)'].values
            y_data_dict[protocol] = protocol_data['TotalTime(ms)'].values
    
    if x_data is not None and len(y_data_dict) > 0:
        # 標準偏差を計算
        delay_std = bw_data.groupby(['Protocol', 'NetworkDelay(ms)'])['TotalTime(ms)'].std().reset_index()
        y_std_dict = {}
        for protocol in ['HTTP/2.0', 'HTTP/3.0']:
            protocol_std = delay_std[delay_std['Protocol'] == protocol].sort_values('NetworkDelay(ms)')
            if not protocol_std.empty:
                y_std_dict[protocol] = protocol_std['TotalTime(ms)'].values
        
        plot_single_graph(ax, x_data, y_data_dict, 
                         'ネットワーク遅延 (ms)', '平均Response Time (ms)', 
                         f'Response Time比較 - {bandwidth_name}',
                         COLORS, show_labels=True, fill_area=False, label_unit='ms', y_std_dict=y_std_dict if y_std_dict else None)
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, 'response_time_comparison.png')
    plt.savefig(output_file, dpi=300, 
                bbox_inches='tight', facecolor='white', pad_inches=0.2)
    print(f"Saved: {output_file}")
    plt.close()

def generate_crossover_analysis_report(df, output_dir):
    """逆転地点分析レポートを生成（crossover_analysis_report.txt）"""
    report_path = os.path.join(output_dir, 'crossover_analysis_report.txt')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("HTTP/2 vs HTTP/3 Performance Crossover Analysis Report\n")
        f.write("逆転地点分析レポート\n")
        f.write("=" * 80 + "\n\n")
        
        # 帯域幅ごとの逆転地点サマリー
        for bandwidth in sorted(df['Bandwidth'].unique()):
            bandwidth_name = bandwidth if bandwidth != '0' else '無制限'
            if bandwidth == '1mbit':
                bandwidth_name = '1Mbps'
            elif bandwidth == '2mbit':
                bandwidth_name = '2Mbps'
            elif bandwidth == '3mbit':
                bandwidth_name = '3Mbps'
            
            bw_data = df[df['Bandwidth'] == bandwidth]
            f.write(f"\n{'=' * 80}\n")
            f.write(f"帯域幅: {bandwidth_name}\n")
            f.write(f"{'=' * 80}\n")
            
            # TTFBの逆転地点
            ttfb_crossovers = find_crossover_points(bw_data, 'TTFB(ms)')
            if ttfb_crossovers:
                f.write("\nTTFB (Time To First Byte) 逆転地点:\n")
                f.write("-" * 80 + "\n")
                for cp in ttfb_crossovers:
                    f.write(f"  {cp['direction']}\n")
                    f.write(f"    推定遅延: {cp['delay']:.1f}ms\n")
                    f.write(f"    HTTP/2: {cp['http2_value']:.3f} ms\n")
                    f.write(f"    HTTP/3: {cp['http3_value']:.3f} ms\n")
                    f.write(f"    差: {abs(cp['http2_value'] - cp['http3_value']):.3f} ms\n")
            else:
                f.write("\nTTFB: 逆転地点は見つかりませんでした\n")
            
            # Total Timeの逆転地点
            total_crossovers = find_crossover_points(bw_data, 'TotalTime(ms)')
            if total_crossovers:
                f.write("\nTotal Time (Response Time) 逆転地点:\n")
                f.write("-" * 80 + "\n")
                for cp in total_crossovers:
                    f.write(f"  {cp['direction']}\n")
                    f.write(f"    推定遅延: {cp['delay']:.1f}ms\n")
                    f.write(f"    HTTP/2: {cp['http2_value']:.3f} ms\n")
                    f.write(f"    HTTP/3: {cp['http3_value']:.3f} ms\n")
                    f.write(f"    差: {abs(cp['http2_value'] - cp['http3_value']):.3f} ms\n")
            else:
                f.write("\nTotal Time: 逆転地点は見つかりませんでした\n")
    
    print(f"Saved: {report_path}")

def plot_crossover_points_summary(df, output_dir):
    """逆転地点サマリー画像を生成（crossover_points_summary.png）"""
    fig, axes = plt.subplots(2, 1, figsize=(14, 12))
    fig.patch.set_facecolor(COLORS['background'])
    
    bandwidths = sorted(df['Bandwidth'].unique())
    bandwidth_names = []
    for bw in bandwidths:
        if bw == '0':
            bandwidth_names.append('無制限')
        elif bw == '1mbit':
            bandwidth_names.append('1Mbps')
        elif bw == '2mbit':
            bandwidth_names.append('2Mbps')
        elif bw == '3mbit':
            bandwidth_names.append('3Mbps')
        else:
            bandwidth_names.append(str(bw))
    
    # TTFBの逆転地点
    ax1 = axes[0]
    ax1.set_facecolor(COLORS['background'])
    ax1.grid(True, alpha=0.35, linestyle='--', linewidth=0.8, color=COLORS['grid'], zorder=0)
    
    ttfb_crossover_delays = []
    ttfb_labels = []
    for i, bandwidth in enumerate(bandwidths):
        bw_data = df[df['Bandwidth'] == bandwidth]
        crossovers = find_crossover_points(bw_data, 'TTFB(ms)')
        for cp in crossovers:
            ttfb_crossover_delays.append(cp['delay'])
            ttfb_labels.append(f"{bandwidth_names[i]}\n{cp['delay']:.1f}ms")
    
    if ttfb_crossover_delays:
        ax1.scatter(range(len(ttfb_crossover_delays)), ttfb_crossover_delays, 
                   s=200, c=COLORS['http2']['main'], marker='o', 
                   edgecolors='white', linewidths=2, zorder=5)
        ax1.set_xticks(range(len(ttfb_crossover_delays)))
        ax1.set_xticklabels(ttfb_labels, rotation=45, ha='right', fontsize=10)
        ax1.set_ylabel('遅延 (ms)', fontsize=16, fontweight='bold', color=COLORS['axis'])
        ax1.set_title('TTFB逆転地点', fontsize=20, fontweight='bold', color=COLORS['text'], pad=20)
    
    # Total Timeの逆転地点
    ax2 = axes[1]
    ax2.set_facecolor(COLORS['background'])
    ax2.grid(True, alpha=0.35, linestyle='--', linewidth=0.8, color=COLORS['grid'], zorder=0)
    
    total_crossover_delays = []
    total_labels = []
    for i, bandwidth in enumerate(bandwidths):
        bw_data = df[df['Bandwidth'] == bandwidth]
        crossovers = find_crossover_points(bw_data, 'TotalTime(ms)')
        for cp in crossovers:
            total_crossover_delays.append(cp['delay'])
            total_labels.append(f"{bandwidth_names[i]}\n{cp['delay']:.1f}ms")
    
    if total_crossover_delays:
        ax2.scatter(range(len(total_crossover_delays)), total_crossover_delays, 
                   s=200, c=COLORS['http3']['main'], marker='s', 
                   edgecolors='white', linewidths=2, zorder=5)
        ax2.set_xticks(range(len(total_crossover_delays)))
        ax2.set_xticklabels(total_labels, rotation=45, ha='right', fontsize=10)
        ax2.set_ylabel('遅延 (ms)', fontsize=16, fontweight='bold', color=COLORS['axis'])
        ax2.set_xlabel('帯域幅条件', fontsize=16, fontweight='bold', color=COLORS['axis'])
        ax2.set_title('Total Time逆転地点', fontsize=20, fontweight='bold', color=COLORS['text'], pad=20)
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, 'crossover_points_summary.png')
    plt.savefig(output_file, dpi=300, 
                bbox_inches='tight', facecolor='white', pad_inches=0.2)
    print(f"Saved: {output_file}")
    plt.close()

def generate_summary_report(df, output_dir):
    """総合レポートを生成"""
    report_path = os.path.join(output_dir, '総合レポート.txt')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("HTTP/2 vs HTTP/3 Performance Comparison - 総合レポート\n")
        f.write("=" * 80 + "\n\n")
        
        # 全体統計
        f.write("Overall Statistics:\n")
        f.write("-" * 80 + "\n")
        for protocol in ['HTTP/2.0', 'HTTP/3.0']:
            protocol_data = df[df['Protocol'] == protocol]
            if len(protocol_data) > 0:
                f.write(f"\n{protocol}:\n")
                f.write(f"  Total Requests: {len(protocol_data)}\n")
                f.write(f"  TTFB (avg): {protocol_data['TTFB(ms)'].mean():.3f} ms\n")
                f.write(f"  TTFB (std): {protocol_data['TTFB(ms)'].std():.3f} ms\n")
                f.write(f"  Total Time (avg): {protocol_data['TotalTime(ms)'].mean():.3f} ms\n")
                f.write(f"  Throughput (avg): {protocol_data['Throughput(KB/s)'].mean():.2f} KB/s\n")
        
        # 帯域幅ごとの逆転地点サマリー
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("Performance Crossover Points Summary (逆転地点サマリー):\n")
        f.write("=" * 80 + "\n")
        
        for bandwidth in sorted(df['Bandwidth'].unique()):
            bandwidth_name = bandwidth if bandwidth != '0' else '無制限'
            if bandwidth == '1mbit':
                bandwidth_name = '1Mbps'
            elif bandwidth == '2mbit':
                bandwidth_name = '2Mbps'
            elif bandwidth == '3mbit':
                bandwidth_name = '3Mbps'
            
            bw_data = df[df['Bandwidth'] == bandwidth]
            f.write(f"\n{bandwidth_name}:\n")
            f.write("-" * 80 + "\n")
            
            # TTFBの逆転地点
            ttfb_crossovers = find_crossover_points(bw_data, 'TTFB(ms)')
            if ttfb_crossovers:
                f.write("  TTFB:\n")
                for cp in ttfb_crossovers:
                    f.write(f"    {cp['direction']} @ {cp['delay']:.1f}ms\n")
            else:
                f.write("  TTFB: 逆転地点なし\n")
            
            # Total Timeの逆転地点
            total_crossovers = find_crossover_points(bw_data, 'TotalTime(ms)')
            if total_crossovers:
                f.write("  Total Time:\n")
                for cp in total_crossovers:
                    f.write(f"    {cp['direction']} @ {cp['delay']:.1f}ms\n")
            else:
                f.write("  Total Time: 逆転地点なし\n")
        
        # 条件別統計
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("Performance by Network Conditions:\n")
        f.write("=" * 80 + "\n")
        
        stats = analyze_by_condition(df)
        for _, row in stats.iterrows():
            f.write(f"\nProtocol: {row['Protocol']}, ")
            f.write(f"Delay: {row['NetworkDelay(ms)']}ms, ")
            f.write(f"Bandwidth: {row['Bandwidth']}\n")
            f.write(f"  TTFB: {row[('TTFB(ms)', 'mean')]:.3f} ± {row[('TTFB(ms)', 'std')]:.3f} ms\n")
            f.write(f"  Total Time: {row[('TotalTime(ms)', 'mean')]:.3f} ± {row[('TotalTime(ms)', 'std')]:.3f} ms\n")
            f.write(f"  Throughput: {row[('Throughput(KB/s)', 'mean')]:.2f} ± {row[('Throughput(KB/s)', 'std')]:.2f} KB/s\n")
    
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
        
        # 全体のグラフを生成（セッションディレクトリのanalysisフォルダに）
        try:
            plot_ttfb_comparison(df, output_dir)
        except Exception as e:
            print(f"Warning: Failed to generate TTFB comparison: {e}")
        
        try:
            plot_throughput_comparison(df, output_dir)
        except Exception as e:
            print(f"Warning: Failed to generate throughput comparison: {e}")
        
        try:
            print("Generating Total Time comparison graph...")
            plot_total_time_comparison(df, output_dir)
            print("Total Time comparison graph generated successfully!")
        except Exception as e:
            print(f"Warning: Failed to generate Total Time comparison: {e}")
            import traceback
            traceback.print_exc()
        
        # 帯域幅ごとのレポート、CSV、グラフを生成
        for bandwidth in sorted(df['Bandwidth'].unique()):
            try:
                # 帯域幅ディレクトリを探す
                bandwidth_name = bandwidth if bandwidth != '0' else '無制限'
                if bandwidth == '1mbit':
                    bandwidth_name = '1Mbps'
                elif bandwidth == '2mbit':
                    bandwidth_name = '2Mbps'
                elif bandwidth == '3mbit':
                    bandwidth_name = '3Mbps'
                
                bw_dir = os.path.join(results_dir, bandwidth_name)
                if not os.path.exists(bw_dir):
                    # ディレクトリが存在しない場合は作成
                    os.makedirs(bw_dir, exist_ok=True)
                
                # 1. CSVファイルを集約
                print(f"\nConsolidating CSV files for {bandwidth_name}...")
                consolidate_bandwidth_csv(results_dir, bandwidth, bw_dir, df)
                
                # 2. 詳細分析レポートを生成
                print(f"Generating detailed analysis report for {bandwidth_name}...")
                generate_bandwidth_report(df, bandwidth, bw_dir)
                
                # 3. Response Time比較グラフを生成
                print(f"Generating response time comparison graph for {bandwidth_name}...")
                plot_bandwidth_response_time_comparison(df, bandwidth, bw_dir)
                
            except Exception as e:
                print(f"Warning: Failed to generate reports for {bandwidth}: {e}")
                import traceback
                traceback.print_exc()
        
        # ルートレベルに逆転地点分析を生成
        print("\nGenerating crossover analysis...")
        try:
            generate_crossover_analysis_report(df, results_dir)
        except Exception as e:
            print(f"Warning: Failed to generate crossover analysis report: {e}")
            import traceback
            traceback.print_exc()
        
        try:
            plot_crossover_points_summary(df, results_dir)
        except Exception as e:
            print(f"Warning: Failed to generate crossover points summary: {e}")
            import traceback
            traceback.print_exc()
        
        # 総合レポートを生成（analysisディレクトリに）
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

