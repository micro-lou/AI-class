package cn.enilu.flash.bean.vo;

import lombok.Data;
import org.hibernate.annotations.Table;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.EntityListeners;
import javax.persistence.Id;
import java.sql.Timestamp;

/**
 * Created  on 2018/4/2 0002.
 *
 * @author enilu
 */
@Data
public class MatchesVo {
    private Integer matchId;
    private String matchType;
    private String matchTime;
    private String refereeName;
    private String red_1;
    private String red_2;
    private String blue_1;;
    private String blue_2;
    private Integer redPoints;
    private Integer bluePoints;
    private Integer isValid ;
    private String winner;

}
