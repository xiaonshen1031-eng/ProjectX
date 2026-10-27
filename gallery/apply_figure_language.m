function apply_figure_language(fig,language)
% Use separate font runs for CJK text and Latin letters / numerals.
root=fileparts(fileparts(mfilename('fullpath')));
registry=jsondecode(fileread(fullfile(root,'gallery','figure-language.json')));
registry.labels=pair_table(registry.labels);registry.patterns=pair_table(registry.patterns);
objects=findall(fig,'-property','FontName');
for k=1:numel(objects)
    objects(k).FontName='Times New Roman';
    if isprop(objects(k),'FontWeight'),objects(k).FontWeight='normal';end
    if isprop(objects(k),'FontAngle'),objects(k).FontAngle='normal';end
end
axesObjects=findall(fig,'Type','axes');
for k=1:numel(axesObjects)
    a=axesObjects(k);a.TickLabelInterpreter='tex';
    for name={'XTickLabel','YTickLabel','ZTickLabel'}
        a.(name{1})=localize(a.(name{1}),language,registry);
    end
end
objects=findall(fig,'-property','String');
for k=1:numel(objects)
    object=objects(k);
    if isprop(object,'Interpreter'),object.Interpreter='tex';end
    object.String=localize(object.String,language,registry);
end
drawnow;
end

function pairs=pair_table(value)
if size(value,2)==2,pairs=value;return;end
pairs=cell(numel(value),2);
for j=1:numel(value),row=value{j};pairs{j,1}=row{1};pairs{j,2}=row{2};end
end

function value=localize(value,language,registry)
if iscell(value)
    value=cellfun(@(s)localize(s,language,registry),value,'UniformOutput',false);return
elseif isstring(value)
    value=string(arrayfun(@(s)localize(char(s),language,registry),value,'UniformOutput',false));return
elseif ~ischar(value)
    return
elseif size(value,1)>1
    value=localize(cellstr(value),language,registry);return
end
if contains(value,'\fontname'),return;end
if strcmp(language,'zh')
    found=false;
    for j=1:size(registry.labels,1)
        if strcmp(value,registry.labels{j,1}),value=registry.labels{j,2};found=true;break;end
    end
    if ~found
        for j=1:size(registry.patterns,1)
            value=regexprep(value,registry.patterns{j,1},registry.patterns{j,2});
        end
    end
end
codes=double(value);
mask=(codes>=hex2dec('3400')&codes<=hex2dec('9FFF'))| ...
     (codes>=hex2dec('3000')&codes<=hex2dec('303F'))| ...
     (codes>=hex2dec('FF00')&codes<=hex2dec('FFEF'));
starts=find(diff([false mask])==1);ends=find(diff([mask false])==-1);
if isempty(starts),return;end
parts={};cursor=1;
for j=1:numel(starts)
    parts{end+1}=value(cursor:starts(j)-1); %#ok<AGROW>
    parts{end+1}=['\fontname{Microsoft YaHei}\bf ' value(starts(j):ends(j)) '\fontname{Times New Roman}\rm ']; %#ok<AGROW>
    cursor=ends(j)+1;
end
parts{end+1}=value(cursor:end);value=[parts{:}];
end
