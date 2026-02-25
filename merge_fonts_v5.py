import os
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

def physical_bolden(glyph_set, glyph_name, amount=20):
    """通过平移合并实现物理加粗"""
    try:
        # 记录原始路径
        rec_pen = RecordingPen()
        glyph_set[glyph_name].draw(rec_pen)
        
        # 创建新字形笔
        tt_pen = TTGlyphPen(glyph_set)
        
        # 绘制原始路径
        for operator, operands in rec_pen.value:
            getattr(tt_pen, operator)(*operands)
            
        # 绘制向右平移后的路径
        for operator, operands in rec_pen.value:
            new_operands = []
            for op in operands:
                if isinstance(op, tuple):
                    new_operands.append((op[0] + amount, op[1]))
                else:
                    new_operands.append(op) # 这种情况通常不会在绘图操作中出现
            getattr(tt_pen, operator)(*new_operands)
            
        return tt_pen.glyph()
    except:
        return None

def merge_fonts_v5(base_path, fallback_path, output_path):
    print(f"Loading fonts...")
    base_font = TTFont(base_path)
    base_cmap = base_font.getBestCmap()
    
    fallback_font = TTFont(fallback_path)
    fallback_cmap = fallback_font.getBestCmap()
    fallback_glyph_set = fallback_font.getGlyphSet()
    
    scale = 1024 / 1000
    
    # 找出 fallback 中有但 base 中没有的字符
    codes_to_bold = set(fallback_cmap.keys()) - set(base_cmap.keys())
    print(f"Codes to bold: {len(codes_to_bold)}")

    # 1. 物理加粗 fallback 中的字符
    for code in codes_to_bold:
        name = fallback_cmap[code]
        new_glyph = physical_bolden(fallback_glyph_set, name, amount=30)
        if new_glyph:
            fallback_font['glyf'][name] = new_glyph
            # 增加宽度以适应加粗
            w, lsb = fallback_font['hmtx'][name]
            fallback_font['hmtx'][name] = (w + 30, lsb)

    # 2. 用 base 覆盖 fallback
    for code, glyph_name in base_cmap.items():
        if code in fallback_cmap:
            target_name = fallback_cmap[code]
            fallback_font['glyf'][target_name] = base_font['glyf'][glyph_name]
            width, lsb = base_font['hmtx'][glyph_name]
            fallback_font['hmtx'][target_name] = (int(width * scale), int(lsb * scale))

    # 3. 更新元数据
    fallback_font['OS/2'].usWeightClass = 700
    name_table = fallback_font['name']
    font_name = "Minecraft Ten Unicode Bold"
    for record in name_table.names:
        if record.nameID in [1, 4, 16]:
            record.string = font_name.encode('utf-16-be')
        elif record.nameID == 2:
            record.string = "Bold".encode('utf-16-be')
        elif record.nameID == 6:
            record.string = "MinecraftTenUnicode-Bold".encode('ascii')

    print(f"Saving...")
    fallback_font.save(output_path)
    print("Done!")

if __name__ == "__main__":
    merge_fonts_v5("user_font/MinecraftTen-VGORe.ttf", "Unifont.ttf", "MinecraftTenUnicode_Final.ttf")
