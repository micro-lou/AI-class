package cn.enilu.flash.bean.entity.system;

import cn.enilu.flash.bean.entity.BaseEntity;
import lombok.Data;
import org.hibernate.annotations.Table;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.EntityListeners;
import javax.persistence.Id;
import java.util.Date;

/**
 * Created  on 2018/4/2 0002.
 *
 * @author enilu
 */
@Entity(name = "score_changes")
@Table(appliesTo = "score_changes", comment = "积分变动")
@Data
@EntityListeners(AuditingEntityListener.class)
public class ScoreChanges {

    @Id
    @Column
    private Integer id;

    @Column
    private Integer playerId;  //INT NOT NULL,

    @Column
    private Integer matchId;   //INT NOT NULL,

    @Column
    private Integer cycleStart;   //DATE NOT NULL COMMENT '周期开始日期（每周日）',

    @Column
    private Integer cycleLength;    //INT NOT NULL COMMENT '周期长度',

    @Column
    private Date seasonStart;      //DATE NOT NULL COMMENT '赛季开始日期',

    @Column
    private Integer seasonLength;   //INT NOT NULL COMMENT '赛季长度',

    @Column
    private Integer pointsChange;        //INT NOT NULL COMMENT '积分变动值'

    @Column
    private Integer pointsAfter;            //INT NOT NULL COMMENT '变动后积分',

    @Column
    private Integer isSettled;           // TINYINT(1) NOT NULL DEFAULT 0 COMMENT '结算状态（0=未结算，1=已结算）'
}
