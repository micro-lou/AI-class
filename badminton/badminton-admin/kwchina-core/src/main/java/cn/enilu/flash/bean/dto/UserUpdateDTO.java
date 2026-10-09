package cn.enilu.flash.bean.dto;
import lombok.Data;
import javax.validation.constraints.NotNull;

@Data
public class UserUpdateDTO {
    @NotNull(message = "用户ID不能为空")
    private Long id;
    private String userName;
    private String playerName;
    private String gender;
    private Integer currentPoints;
    private Integer roleType;
    private String password; // 密码字段（可选更新）
}