import sys

with open('src/network/relations.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换关系合并逻辑
old_merge = """                for item in data:
                    src = item.get("source")
                    tgt = item.get("target")
                    if src in characters and tgt in characters and src != tgt:
                        pair = tuple(sorted([src, tgt]))
                        if pair not in seen_pairs:
                            seen_pairs.add(pair)
                            relations.append(Relation(
                                source=src,
                                target=tgt,
                                type=item.get("type", "association"),
                                context=item.get("context", ""),
                                position=i, # 粗略位置
                                sentiment=float(item.get("sentiment", 0.5))
                            ))
            except Exception as e:
                print(f"  [LLM Extract Error at chunk {i}] {e}")
                
        return relations"""

new_merge = """                for item in data:
                    src = item.get("source")
                    tgt = item.get("target")
                    if src in characters and tgt in characters and src != tgt:
                        pair = tuple(sorted([src, tgt]))
                        
                        # 改为在列表中合并同一对人物的关系（如果类型相同则认为是同一次互动被重复提取）
                        # 这里我们不仅用 pair 区分，还要结合上下文粗略排重，或者允许同一对人物存在多次不同位置的互动
                        # 从而在后续计算动态关系时有更多时间序列数据点
                        # 为了避免滑动窗口重叠区完全相同的提取，我们利用上下文(context)的简单哈希来去重
                        context_snippet = item.get("context", "")
                        unique_interaction_key = f"{pair[0]}_{pair[1]}_{context_snippet[:10]}"
                        
                        if unique_interaction_key not in seen_pairs:
                            seen_pairs.add(unique_interaction_key)
                            relations.append(Relation(
                                source=src,
                                target=tgt,
                                type=item.get("type", "association"),
                                context=context_snippet,
                                position=i, # 粗略位置
                                sentiment=float(item.get("sentiment", 0.5))
                            ))
            except Exception as e:
                print(f"  [LLM Extract Error at chunk {i}] {e}")
                
        return relations"""

if old_merge in content:
    content = content.replace(old_merge, new_merge)
    with open('src/network/relations_fixed2.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Replaced merge logic.')
else:
    print('old_merge not found!')