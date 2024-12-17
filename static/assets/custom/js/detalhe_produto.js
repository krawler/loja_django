$(document).ready(function(){

    Fancybox.bind("[data-fancybox]", {});      

    $("#imagem_produto").ezPlus();    

    $("#descricao_longa").find("p").addClass("lead");
    
    estoques = JSON.parse($('#estoques_variacoes').val());
    saldo_estoque = estoques[$("#select-variacoes").val()];
    $("#saldo_estoque").html(saldo_estoque);
    if(saldo_estoque === 0){
        $("#pergunta_aviso_produto_disponivel").show();
        $("#btnAdicionarCarrinho").addClass('disabled');
    }    

    dimensoesVariacoes = $('#dimensoes').val().replaceAll('\'', '"')
    dimensoesVariacoes = JSON.parse(dimensoesVariacoes);

    $("#select-variacoes").change(function(){
        id_variacao = $(this).val();
        if(estoques[id_variacao] === 0){
            $("#pergunta_aviso_produto_disponivel").show();
            $("#btnAdicionarCarrinho").addClass('disabled');
        }else{
            $("#btnAdicionarCarrinho").removeClass('disabled');
            $("#pergunta_aviso_produto_disponivel").hide();
        }

        $("#saldo_estoque").html(estoques[id_variacao]);

        for(dimensao in dimensoesVariacoes){
            if(dimensoesVariacoes[dimensao].id == $("#select-variacoes").val()){
                $("#desc_largura").html(dimensoesVariacoes[dimensao].largura);
                $("#desc_comprimento").html(dimensoesVariacoes[dimensao].comprimento);
                $("#desc_altura").html(dimensoesVariacoes[dimensao].altura);
                $("#desc_peso").html(dimensoesVariacoes[dimensao].peso);
            }
                
        }
    });

});