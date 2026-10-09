package cn.enilu.flash.bean.entity.system;

import cn.enilu.flash.bean.entity.BaseEntity;
import lombok.Data;
import org.hibernate.annotations.Table;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.EntityListeners;
import javax.persistence.Id;

/**
 * Created  on 2018/4/2 0002.
 *
 * @author enilu
 */
@Entity(name = "player_data")
@Table(appliesTo = "player_data", comment = "选手数据")
@Data
@EntityListeners(AuditingEntityListener.class)
public class ScoreRole {

    @Id
    @Column(columnDefinition = "int COMMENT '规则编号'")
    private Integer roleId;

    @Column(columnDefinition = "int COMMENT '积分挡位下限'")
    private Integer minScore;

    @Column(columnDefinition = "int COMMENT '积分挡位上限'")
    private Integer calRule;

    @Column(columnDefinition = "int COMMENT '是否是固定分值，如果是固定分值，不计算，直接加'")
    private int isFix;

    @Column(columnDefinition = "int COMMENT '败者积分常数 ,固定分的情况下，此为败者的加分'")
    private float score;

    @Column(columnDefinition = "int COMMENT '运算符'")
    private String calSymbol;

    @Column(columnDefinition = "int COMMENT '每周同对手期场次上限'")
    private Integer cycleSameMax;

    @Column(columnDefinition = "int COMMENT '每天同对手期场次上限'")
    private Integer daySameMax;

    @Column(columnDefinition = "int COMMENT '每日场次上限'")
    private Integer dayMax;

    @Column(columnDefinition = "int COMMENT '胜者系数'")
    private Integer k;

}
