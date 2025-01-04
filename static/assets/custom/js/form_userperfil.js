$(document).ready(function(){

    $("#id_cep").after('<button type="button" id="btn_cep" '+ 
                        'class="btn btn-primary mt-2"> '+
                        'Buscar</button>')
                .addClass('relative-field');
    
    $("#btn_cep").click(() => {
        findCep();     
    })                    
    
    $("#id_cep").blur(() => {
        findCep();
    });

    function findCep() {
        let cep = $("#id_cep").val().replace("-", "")
        let url_call = "https://viacep.com.br/ws/" + cep + "/json/"; 
        return $.ajax({
                    url: url_call,
                    type: 'GET',
                    async: true,
                    success: function(response){
                        $("#id_bairro").val(response.bairro);
                        $("#id_cidade").val(response.localidade);
                        $("#id_endereco").val(response.logradouro);
                        $("#uf").val(response.uf);
                    }
                },                
        );
    }

    $("#btn_cep").click(() => {
        let cep = $("#id_cep").val().replace("-", "")
        let url_call = "https://viacep.com.br/ws/" + cep + "/json/"; 
        $.ajax({
                    url: url_call,
                    type: 'GET',
                    async: true,
                    success: function(response){
                        $("#id_bairro").val(response.bairro);
                        $("#id_cidade").val(response.localidade);
                        $("#id_endereco").val(response.logradouro);
                        $("#uf").val(response.uf);
                    }
                },                
        );
    });

    $("#enviar_form_perfil").click((e) => {
        $.ajax({
                    url: url_call,
                    type: 'GET',
                    async: false,
                    success: function(response){
                        if(response.uf != $("#id_estado").val()){
                            e.preventDefault(); 
                            $("#id_cep").css("border-color", "red");
                            $("#id_estado").css("border-color", "red"); 
                            $("#id_estado").after('<span class="password-strength-indicator"' 
                                                + 'style="display: none;">&nbsp;</span>')
                                            .after('<small id="hint_id_password"'
                                                + ' class="form-text text-red-validation">O estado deve ser' 
                                                + ' o mesmo estado do cep</small>');                            } 
                    }
                },                
        );
    });
        
    $('#perfil_endereco').change(function() {
        if ($(this).is(':checked')) {
            habilitaCamposPerfil();
        } else {
            desabilitaCamposPerfil();
        }
    });

});

function desabilitaCamposPerfil() {
    $("#id_numero").prop("disabled", true);
    $("#id_bairro").prop("disabled", true);
    $("#id_endereco").prop("disabled", true);
    $("#id_cep").prop("disabled", true);
    $("#id_complemento").prop("disabled", true); 
    $("#id_cidade").prop("disabled", true); 
    $("#id_estado").prop("disabled", true);
    $("#btn_cep").addClass("disabled");
    $("#id_nome_completo").focus();
}

function habilitaCamposPerfil() {
    $("#id_numero").prop("disabled", false);
    $("#id_bairro").prop("disabled", false);
    $("#id_endereco").prop("disabled", false);
    $("#id_cep").prop("disabled", false);
    $("#id_complemento").prop("disabled", false); 
    $("#id_cidade").prop("disabled", false); 
    $("#id_estado").prop("disabled", false);
    $("#id_nome_completo").prop("disabled", false);
    $("#btn_cep").removeClass("disabled");
    $("#id_cep").focus();
}