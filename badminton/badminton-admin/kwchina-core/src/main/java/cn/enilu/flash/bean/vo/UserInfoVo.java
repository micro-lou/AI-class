package cn.enilu.flash.bean.vo;

import lombok.Data;

import java.util.Date;

/**
 * @author ：enilu
 * @date ：Created in 11/6/2019 11:29 AM
 */
@Data
public class UserInfoVo {
    private Long id;

    private String playerName;

    private String gender;

    private String userName;

    private Integer roleType;

}
