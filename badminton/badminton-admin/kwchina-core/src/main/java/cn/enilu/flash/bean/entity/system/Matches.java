package cn.enilu.flash.bean.entity.system;

import cn.enilu.flash.bean.entity.BaseEntity;
import lombok.Data;
import org.hibernate.annotations.Table;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.EntityListeners;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import java.sql.Date;
import java.sql.Timestamp;
import java.time.LocalDateTime;

/**
 * Created  on 2018/4/2 0002.
 *
 * @author enilu
 */
@Entity(name = "matches")
@Table(appliesTo = "matches", comment = "比赛")
@Data
@EntityListeners(AuditingEntityListener.class)
public class Matches {

    @Id
    @GeneratedValue
    @Column(columnDefinition = "int COMMENT '比赛编号'", unique = true, nullable = false)
    private Integer matchId;

    @Column(columnDefinition = "ENUM('单打', '双打') COMMENT '比赛类型'", unique = false, nullable = false)
    private String matchType;

    @Column(columnDefinition = "Datetime COMMENT '比赛时间'", unique = false, nullable = false)
    private LocalDateTime matchTime;

    @Column(columnDefinition = "int COMMENT '裁判编号'", unique = false, nullable = false)
    private String refereeName;

    @Column(columnDefinition = "int COMMENT '红一编号'", unique = false, nullable = false)
    private String red_1;

    @Column(columnDefinition = "int COMMENT '红二编号'", unique = false, nullable = false)
    private String red_2;

    @Column(columnDefinition = "int COMMENT '蓝一编号'", unique = false, nullable = false)
    private String blue_1;

    @Column(columnDefinition = "int COMMENT '蓝二编号'", unique = false, nullable = false)
    private String blue_2;

    @Column(columnDefinition = "int COMMENT '红方得分'", unique = false, nullable = false)
    private Integer redPoints;

    @Column(columnDefinition = "int COMMENT '蓝方得分'", unique = false, nullable = false)
    private Integer bluePoints;

    @Column(columnDefinition = "ENUM('red', 'blue') COMMENT '获胜方'", unique = false, nullable = false)
    private String winner;

    @Column(columnDefinition = "int COMMENT '是否积分'", unique = false, nullable = false)
    private Integer isValid;

    @Column(columnDefinition = "int COMMENT '积分结算时间'", nullable = false)
    private String settlementTime;

    @Column(columnDefinition = "记录时间", nullable = false)
    private LocalDateTime recordTime;

}
