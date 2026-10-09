package cn.enilu.flash.bean.entity.system;

import cn.enilu.flash.bean.entity.BaseEntity;


import lombok.Data;
import org.hibernate.annotations.Table;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.EntityListeners;


/**
 * Created  on 2018/4/2 0002.
 *
 * @author enilu
 */
@Entity(name = "users")
@Table(appliesTo = "users",comment = "用户")
@Data
@EntityListeners(AuditingEntityListener.class)
public class Users  extends BaseEntity {

    @Column( columnDefinition = "VARCHAR(50) COMMENT '选手姓名'")
    private String playerName;

    @Column
    private String gender;

    @Column(name = "initial_points")
    private Integer initialPoints ;

    @Column(name = "current_points")
    private Integer currentPoints  ;

    @Column
    private String userName;

    @Column
    private String password;

    @Column
    private Integer roleType;

    @Column
    private Integer userType;

    private String salt;




}
