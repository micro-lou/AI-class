package cn.enilu.flash.bean.entity.system;

import lombok.Data;
import org.hibernate.annotations.Table;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import javax.persistence.Id;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.EntityListeners;

/**
 * Created  on 2018/4/2 0002.
 *
 * @author enilu
 */
@Entity(name = "player_data")
@Table(appliesTo = "player_data", comment = "选手数据")
@Data
@EntityListeners(AuditingEntityListener.class)
public class playerData {
    @Id
    @Column(columnDefinition = "int COMMENT '选手编号'", unique = true, nullable = false)
    private Long id;

    @Column(columnDefinition = "int COMMENT '单打总得分'")
    private Integer totalSscore;

    @Column(columnDefinition = "int COMMENT '双打总得分'")
    private Integer totalDscore;

    @Column(columnDefinition = "int COMMENT '单打总场次'")
    private Integer singleMatches;

    @Column(columnDefinition = "int COMMENT '双打总场次'", name = "doubleMatches")
    private Integer doubleMatches;

    @Column(columnDefinition = "int COMMENT '单打总胜场'")
    private Integer singleWin;

    @Column(columnDefinition = "int COMMENT '双打总胜场'")
    private Integer doubleWin;

}
