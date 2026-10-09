package cn.enilu.flash.bean.vo;

import cn.enilu.flash.utils.StringUtil;
import lombok.Data;

import javax.persistence.Column;
import java.util.Date;

/**
 * @author ：enilu
 * @date ：Created in 11/6/2019 11:29 AM
 */
@Data
public class UserInfo {
    private Long id;
    private String avatar;
    private String account;
    private String name;
    private Date birthday;
    private Integer sex;
    private String email;
    private String phone;
    private String roleid;
    private Long deptid;
}
