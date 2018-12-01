function login(){
    var $user = $("#user"),
        $pass = $("#pass")
        if(!$user.val()){
            swal("温馨提示", "用户名不允许为空")
        }else if(!$pass.val()){
            swal("温馨提示", "密码不允许为空")
        }else if($pass.val().length<8){
            swal("温馨提示", "密码最短为8位数")
        }else{
            $.ajax({ 
                url: "/login/",
                type :'POST',
                data :
                    {
                        'username': $user.val(),
                        'password': $pass.val(),
                        'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
                    },
                dataType : 'json',
                success: function(resp){
                    switch(resp.error){
                        case 0:
                            swal({ 
                                title: "登录成功！", 
                                text: "干得漂亮！。", 
                                timer: 2000, 
                                showConfirmButton: false 
                            });
                            window.location.href = resp.url;
                            break;
                        case 1:
                            swal('温馨提示', resp.msg)
                            break;
                        case 2:
                            swal('温馨提示', resp.msg)
                            break;
                        default:
                            swal('温馨提示', '进入了more')
                            break;
                        }
                    },
                error: function(info) {
                    swal("错误","error");
                }
            });
        }
}

function register(){
    var $username = $("#username"),
        $password = $("#password"),
        $confirm_password = $("#confirm_password"),
        $email = $("#email");

    if(!$username.val()){
        swal("温馨提示", "用户名不允许为空","error")
    }else if(!$password.val()){
        swal("温馨提示", "密码不允许为空","error")
    }else if($password.val().length<8){
        swal("温馨提示", "密码最短为8位数","error")
    }else if($confirm_password.val().length<8){
        swal("温馨提示", "请填写确认密码","error")
    }else if($password.val() != $confirm_password.val()){
        swal("温馨提示", "输入的密码不相同","error")
    }else if(!$email.val()){
        swal("温馨提示", "请填写邮箱","error")
    }
    else{
        $.ajax({ 
            url: "/register/",
            type :'POST',
            data :
                {
                    'username':$username.val(),
                    'password':$password.val(),
                    'confirm_password':$confirm_password.val(),
                    'email':$email.val(),
                    'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
                },
            dataType : 'json',
            success: function(resp){
                switch(resp.error){
                    case 0:
                            swal("干得漂亮！", "注册成功！","success")
                            window.location.href = '/login/';
                        break;
                    case 1:
                        swal('温馨提示', resp.msg)
                        break;
                    default:
                        swal('温馨提示', '进入了more')
                        break;
                    }
                },
            error: function(info) {
                swal("错误","error");
            }
        });
    }
}

$(function(){
    $("#login_form input[type='button']").on('click', login)
    $("#user_form input[type='button']").on('click', register)
})