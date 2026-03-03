import hashlib

def build_j_password_final(password: str) -> str:
    suffix = "{Urp602019}"
    
    # 模拟 hex_md5(s) -> 带后缀
    def hex_md5_default(s):
        return hashlib.md5((s + suffix).encode("utf-8")).hexdigest()
    
    # 模拟 hex_md5(s, '1.8') -> 标准 md5
    def hex_md5_v18(s):
        return hashlib.md5(s.encode("utf-8")).hexdigest()

    # 严格对应 onclick 逻辑:
    # hex_md5(hex_md5(p), '1.8') + '*' + hex_md5(hex_md5(p, '1.8'), '1.8')
    part_left = hex_md5_v18(hex_md5_default(password))
    part_right = hex_md5_v18(hex_md5_v18(password))
    
    return f"{part_left}*{part_right}"

# 测试

# 你可以自己去抓一下前端给的信息 测试一下 验证一下加密方法对不对

# style="background: #56baed;margin-bottom:10px;" class="fadeIn fourth" value="登 录" onclick="$('#input_password').val( hex_md5(hex_md5($('#input_password').val()), '1.8') + '*' + hex_md5(hex_md5($('#input_password').val(), '1.8'), '1.8'));">