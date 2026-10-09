package cn.enilu.flash.mobile.controller;

import cn.enilu.flash.bean.constant.state.ManagerStatus;
import cn.enilu.flash.bean.entity.shop.ShopUser;
import cn.enilu.flash.bean.entity.system.User;
import cn.enilu.flash.bean.vo.JwtUser;
import cn.enilu.flash.bean.vo.UserInfo;
import cn.enilu.flash.bean.vo.front.Rets;
import cn.enilu.flash.bean.vo.shop.WechatInfo;
import cn.enilu.flash.cache.CacheDao;
import cn.enilu.flash.core.log.LogManager;
import cn.enilu.flash.core.log.LogTaskFactory;
import cn.enilu.flash.security.UserService;
import cn.enilu.flash.service.ApplicationProperties;
import cn.enilu.flash.service.shop.ShopUserService;
import cn.enilu.flash.service.system.ManagerService;
import cn.enilu.flash.utils.*;
import cn.enilu.flash.web.controller.BaseController;
import io.swagger.annotations.ApiOperation;
import net.sf.ehcache.CacheManager;
import net.sf.ehcache.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.ehcache.EhCacheCacheManager;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.Collectors;

/**
 * @author ：enilu
 * @date ：Created in 11/5/2019 9:01 PM
 */
@RestController
@RequestMapping("/")
public class LoginController extends BaseController {
    @Autowired
    private ShopUserService shopUserService;
    @Autowired
    private UserService userService;
    @Autowired
    private CacheDao cacheDao;
    @Autowired
    private ApplicationProperties applicationProperties;
    private Logger logger = LoggerFactory.getLogger(LoginController.class);
    @Autowired
    private ManagerService managerService;

    @Resource
    EhCacheCacheManager ehCacheCacheManager;


    @ApiOperation("使用手机号和密码登录")
    @RequestMapping(value = "loginByPass", method = RequestMethod.POST)
    public Object loginByPass(@RequestParam String mobile, @RequestParam String password) {
        try {
            logger.info("用户登录:" + mobile + ",密码:" + password);
            //1,
            User user = managerService.findByAccount(mobile);
            if (user == null) {
                return Rets.failure("该用户不存在");
            }
            LocalDateTime thirtyMinutesAgo = LocalDateTime.now().minus(15, ChronoUnit.MINUTES);
            Instant instant = thirtyMinutesAgo.atZone(ZoneId.systemDefault()).toInstant();
            // 转换为java.util.Date
            Date thirtyMinutesDate = Date.from(instant);
            if (user.getStatus().equals(ManagerStatus.FREEZED.getCode())&&user.getLockTime().isAfter(thirtyMinutesAgo)) {
                return Rets.failure("账号已锁定，请15分钟后尝试");
            } else if(user.getStatus() == ManagerStatus.DELETED.getCode()){
                return Rets.failure("用户已删除");
            }
            password = CryptUtil.desEncrypt(password);
            String passwdMd5 = MD5.md5(password, user.getSalt());
            //2,
            if (!user.getPassword().equals(passwdMd5)) {
                if(!setAttemptTime(mobile)){
                    LockAccount(user);
                    return Rets.failure("账号已锁定，请15分钟后尝试");
                }
                return Rets.failure("输入的密码错误");
            }
            if(user.getStatus().equals(ManagerStatus.FREEZED.getCode())){
                unLockAccount(user);
            }

            String token = userService.loginForToken(new JwtUser(user));
            Map<String, Object> result = new HashMap<>(1);
            logger.info("token:{}",token);
            result.put("token", token);
            UserInfo userInfo = new UserInfo();
            BeanUtils.copyProperties(user, userInfo);
            result.put("user", userInfo);
            LogManager.me().executeLog(LogTaskFactory.loginLog(user.getId(), HttpUtil.getIp()));
            return Rets.success(result);
        } catch (Exception e) {
            logger.error(e.getMessage(), e);
        }
        return Rets.failure("登录时失败");

       /* try {
            logger.info("用户登录:" + mobile + ",密码:" + password);
            //1,
            ShopUser user = shopUserService.findByMobile(mobile);
            if (user == null) {
                return Rets.failure("该用户不存在");
            }
            try {
                password = CryptUtil.desEncrypt(password);
            }catch (Exception e){}
            String passwdMd5 = MD5.md5(password, user.getSalt());

            //2,
            if (!user.getPassword().equals(passwdMd5)) {
                return Rets.failure("输入的密码错误");
            }
            String token = userService.loginForToken(new JwtUser(user));
            Map<String, Object> result = new HashMap<>(1);
            user.setLastLoginTime(new Date());
            shopUserService.update(user);
            UserInfo userInfo = new UserInfo();
            BeanUtils.copyProperties(user, userInfo);

            logger.info("token:{}", token);
            result.put("token", token);
            result.put("user", userInfo);
            return Rets.success(result);
        } catch (Exception e) {
            logger.error(e.getMessage(), e);
        }
        return Rets.failure("登录时失败");*/
    }

    /**
     * 退出登录
     *
     * @return
     */
    @RequestMapping(value = "/logout", method = RequestMethod.POST)
    public Object logout() {
        logger.info("处理额外的退出登录逻辑");
        return Rets.success();
    }


    //是否可以继续登录
    private boolean setAttemptTime(String account){
        CacheManager cacheManager = ehCacheCacheManager.getCacheManager();
        String now=LocalDateTimeUtil.format(LocalDateTime.now(),"yyyy-MM-dd HH:mm:ss");
        List<String> newAttemptTimes=new ArrayList<>();
        if(cacheManager.getCache("attemptTimes")!=null&&cacheManager.getCache("attemptTimes").get(account)!=null){
            Element attemptTimes= cacheManager.getCache("attemptTimes").get(account);
            List<String> times = (List<String>)attemptTimes.getObjectValue();
            String towMinutes=LocalDateTimeUtil.format(LocalDateTime.now().minusMinutes(2),"yyyy-MM-dd HH:mm:ss");

            //取两分钟之内的登录错误的数据
            newAttemptTimes=times.stream().filter(e->e.compareTo(towMinutes)>0).collect(Collectors.toList());
            if (newAttemptTimes.size()==4){
                return false;
            }
        }
        newAttemptTimes.add(now);
        if(cacheManager.getCache("attemptTimes")==null){
            cacheManager.addCache("attemptTimes");
        }
        cacheManager.getCache("attemptTimes").put(new Element(account,newAttemptTimes));
        return true;
    }

    private void LockAccount(User sysUser) {
        CacheManager cacheManager = ehCacheCacheManager.getCacheManager();
        cacheManager.getCache("attemptTimes").remove(sysUser.getAccount());
        sysUser.setStatus(ManagerStatus.FREEZED.getCode());
        sysUser.setLockTime(LocalDateTime.now());
        managerService.update(sysUser);
    }

    private void unLockAccount(User sysUser) {
        //删除缓存
        CacheManager cacheManager = ehCacheCacheManager.getCacheManager();
        if(cacheManager.getCache("attemptTimes")!=null&&cacheManager.getCache("attemptTimes").get(sysUser.getAccount())!=null){
            cacheManager.getCache("attemptTimes").remove(sysUser.getAccount());
        }

        sysUser.setStatus(ManagerStatus.OK.getCode());
        managerService.update(sysUser);
    }
}
