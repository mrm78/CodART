import os

from gen.javaLabeled.JavaLexer import JavaLexer

# try:
#     import understand as und
# except ImportError as e:
#     print(e)
from utilization.setup_understand import *

from antlr4 import *
from antlr4.TokenStreamRewriter import TokenStreamRewriter

from gen.javaLabeled.JavaParserLabeled import JavaParserLabeled
from gen.javaLabeled.JavaParserLabeledListener import JavaParserLabeledListener


class ExtractSubClassRefactoringListener(JavaParserLabeledListener):
    """
    To implement extract class refactoring based on its actors.
    Creates a new class and move fields and methods from the old class to the new one
    """

    def __init__(
            self, common_token_stream: CommonTokenStream = None,
            source_class: str = None, new_class: str = None,
            moved_fields=None, moved_methods=None,
            output_path: str = ""):

        if moved_methods is None:
            self.moved_methods = []
        else:
            self.moved_methods = moved_methods
        if moved_fields is None:
            self.moved_fields = []
        else:
            self.moved_fields = moved_fields

        if common_token_stream is None:
            raise ValueError('common_token_stream is None')
        else:
            self.token_stream_rewriter = TokenStreamRewriter(common_token_stream)

        if source_class is None:
            raise ValueError("source_class is None")
        else:
            self.source_class = source_class
        if new_class is None:
            raise ValueError("new_class is None")
        else:
            self.new_class = new_class

        self.output_path = output_path

        self.is_source_class = False
        self.detected_field = None
        self.detected_method = None
        self.TAB = "\t"
        self.NEW_LINE = "\n"
        self.code = ""
        self.is_in_constructor = False

    def enterClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        """
        It checks if it is source class, we generate the declaration of the new class, by appending some text to self.code.
        """

        class_identifier = ctx.IDENTIFIER().getText()
        if class_identifier == self.source_class:
            self.is_source_class = True
            self.code += self.NEW_LINE * 2
            self.code += f"// New class({self.new_class}) generated by CodART" + self.NEW_LINE
            self.code += f"class {self.new_class} extends {self.source_class}{self.NEW_LINE}" + "{" + self.NEW_LINE
        else:
            self.is_source_class = False

    def exitClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        """
        It close the opened curly brackets If it is the source class.
        """

        if self.is_source_class:
            self.code += "}"
            self.is_source_class = False

    def exitCompilationUnit(self, ctx: JavaParserLabeled.CompilationUnitContext):
        """
        it writes self.code in the output path.​
        """

        # self.token_stream_rewriter.insertAfter(
        #     index=ctx.stop.tokenIndex,
        #     text=self.code
        # )

        child_file_name = self.new_class + ".java"
        with open(os.path.join(self.output_path, child_file_name), "w+") as f:
            f.write(self.code.replace('\r\n', '\n'))

    def enterVariableDeclaratorId(self, ctx: JavaParserLabeled.VariableDeclaratorIdContext):
        """
        It sets the detected field to the field if it is one of the moved fields. ​
        """

        if not self.is_source_class:
            return None
        field_identifier = ctx.IDENTIFIER().getText()
        if field_identifier in self.moved_fields:
            self.detected_field = field_identifier

    def exitFieldDeclaration(self, ctx: JavaParserLabeled.FieldDeclarationContext):
        """
        It gets the field name, if the field is one of the moved fields, we move it and delete it from the source program. ​
        """

        if not self.is_source_class:
            return None
        # field_names = ctx.variableDeclarators().getText().split(",")
        field_identifier = ctx.variableDeclarators().variableDeclarator(0).variableDeclaratorId().IDENTIFIER().getText()
        field_names = list()
        field_names.append(field_identifier)
        print("field_names=", field_names)
        print("Here")
        grand_parent_ctx = ctx.parentCtx.parentCtx
        if self.detected_field in field_names:
            if (not grand_parent_ctx.modifier()):
                # print("******************************************")
                modifier = ""
            else:
                modifier = grand_parent_ctx.modifier(0).getText()
            field_type = ctx.typeType().getText()
            self.code += f"{self.TAB}{modifier} {field_type} {self.detected_field};{self.NEW_LINE}"
            # delete field from source class
            # field_names.remove(self.detected_field)
            # if field_names:
            #     self.token_stream_rewriter.replaceRange(
            #         from_idx=grand_parent_ctx.start.tokenIndex,
            #         to_idx=grand_parent_ctx.stop.tokenIndex,
            #         text=f"{modifier} {field_type} {','.join(field_names)};"
            #     )
            # else:
            # self.token_stream_rewriter.delete(
            #     program_name=self.token_stream_rewriter.DEFAULT_PROGRAM_NAME,
            #     from_idx=grand_parent_ctx.start.tokenIndex,
            #     to_idx=grand_parent_ctx.stop.tokenIndex
            # )

            # delete field from source class ==>new
            start_index = ctx.parentCtx.parentCtx.start.tokenIndex
            stop_index = ctx.parentCtx.parentCtx.stop.tokenIndex
            self.token_stream_rewriter.delete(
                program_name=self.token_stream_rewriter.DEFAULT_PROGRAM_NAME,
                from_idx=start_index,
                to_idx=stop_index
            )

            self.detected_field = None

    def enterMethodDeclaration(self, ctx: JavaParserLabeled.MethodDeclarationContext):
        """
        It sets the detected field to the method if it is one of the moved methods. ​
        """

        if not self.is_source_class:
            return None
        method_identifier = ctx.IDENTIFIER().getText()
        if method_identifier in self.moved_methods:
            self.detected_method = method_identifier

    def exitMethodDeclaration(self, ctx: JavaParserLabeled.MethodDeclarationContext):
        """
        It gets the method name, if the method is one of the moved methods, we move it to the subclass and delete it from the source program.
        """

        if not self.is_source_class:
            return None
        method_identifier = ctx.IDENTIFIER().getText()
        if self.detected_method == method_identifier:
            # method_modifier = ctx.parentCtx.parentCtx.modifier(0)
            # if(method_modifier!=)
            # method_modifier_text=method_modifier.getText()
            # print(method_modifier_text)

            # start_index = ctx.start.tokenIndex
            start_index = ctx.parentCtx.parentCtx.start.tokenIndex
            stop_index = ctx.stop.tokenIndex
            method_text = self.token_stream_rewriter.getText(
                program_name=self.token_stream_rewriter.DEFAULT_PROGRAM_NAME,
                start=start_index,
                stop=stop_index
            )
            self.code += (self.NEW_LINE + self.TAB + method_text + self.NEW_LINE)
            # delete method from source class
            self.token_stream_rewriter.delete(
                program_name=self.token_stream_rewriter.DEFAULT_PROGRAM_NAME,
                from_idx=start_index,
                to_idx=stop_index
            )
            self.detected_method = None

    def enterConstructorDeclaration(self, ctx: JavaParserLabeled.ConstructorDeclarationContext):
        if self.is_source_class:
            self.is_in_constructor = True
            self.fields_in_constructor = []
            self.methods_in_constructor = []
            self.constructor_body = ctx.block()
            children = self.constructor_body.children
            # for child in children:
            #     if child.getText()=='{' or child.getText()=='}':
            #         continue

    def exitConstructorDeclaration(self, ctx: JavaParserLabeled.ConstructorDeclarationContext):
        if self.is_source_class and self.is_in_constructor:
            move_constructor_flag = False
            for field in self.fields_in_constructor:
                if field in self.moved_fields:
                    move_constructor_flag = True

            for method in self.methods_in_constructor:
                if method in self.moved_methods:
                    move_constructor_flag = True

            if move_constructor_flag:
                # start_index = ctx.parentCtx.parentCtx.start.tokenIndex
                # stop_index = ctx.parentCtx.parentCtx.stop.tokenIndex

                if ctx.formalParameters().formalParameterList():
                    constructor_parameters = [ctx.formalParameters().formalParameterList().children[i] for i in
                                              range(len(ctx.formalParameters().formalParameterList().children)) if
                                              i % 2 == 0]
                else:
                    constructor_parameters = []

                constructor_text = ''
                for modifier in ctx.parentCtx.parentCtx.modifier():
                    constructor_text += modifier.getText() + ' '
                # constructor_text += ctx.IDENTIFIER().getText()#======
                constructor_text += self.new_class
                constructor_text += ' ( '
                for parameter in constructor_parameters:
                    constructor_text += parameter.typeType().getText() + ' '
                    constructor_text += parameter.variableDeclaratorId().getText() + ', '
                if constructor_parameters:
                    constructor_text = constructor_text[:len(constructor_text) - 2]
                constructor_text += ')\n\t{'
                constructor_text += self.token_stream_rewriter.getText(
                    program_name=self.token_stream_rewriter.DEFAULT_PROGRAM_NAME,
                    start=ctx.block().start.tokenIndex + 1,
                    stop=ctx.block().stop.tokenIndex - 1
                )
                constructor_text += '}\n'

                self.code += constructor_text

                start_index = ctx.parentCtx.parentCtx.start.tokenIndex
                stop_index = ctx.parentCtx.parentCtx.stop.tokenIndex
                self.token_stream_rewriter.delete(
                    program_name=self.token_stream_rewriter.DEFAULT_PROGRAM_NAME,
                    from_idx=start_index,
                    to_idx=stop_index
                )

        self.is_in_constructor = False

    def enterExpression21(self, ctx: JavaParserLabeled.Expression21Context):
        if self.is_source_class and self.is_in_constructor:
            if len(ctx.children[0].children) == 1:
                self.fields_in_constructor.append(ctx.children[0].getText())
            else:
                self.fields_in_constructor.append(ctx.children[0].children[-1].getText())

    def enterMethodCall0(self, ctx: JavaParserLabeled.MethodCall0Context):
        if self.is_source_class and self.is_in_constructor:
            self.methods_in_constructor.append(ctx.IDENTIFIER())


"""
Utilities related to project directory.
"""

import os
import subprocess


# def create_understand_database(project_dir, und_path='/home/ali/scitools/bin/linux64/'):
def create_understand_database(project_dir, und_path='C:\\Program Files\\SciTools\\bin\\pc-win64'):
    """
    This function creates understand database for the given project directory.
    :param und_path: The path of und binary file for executing understand command-line
    :param project_dir: The absolute path of project's directory.
    :return: String path of created database.
    """
    assert os.path.isdir(project_dir)
    assert os.path.isdir(und_path)
    db_name = os.path.basename(os.path.normpath(project_dir)) + ".udb"
    db_path = os.path.join(project_dir, db_name)
    assert os.path.exists(db_path) is False
    # An example of command-line is:
    # und create -languages c++ add @myFiles.txt analyze -all myDb.udb
    process = subprocess.Popen(
        ['und', 'create', '-languages', 'Java', 'add', project_dir, 'analyze', '-all', db_path],
        cwd=und_path
    )
    process.wait()
    return db_path


def update_understand_database(udb_path, project_dir=None, und_path='/home/ali/scitools/bin/linux64/'):
    """
    This function updates database due to file changes.
    :param project_dir: If understand database file is not in project directory you can specify the project directory.
    :param und_path: The path of und binary file for executing understand command-line
    :param udb_path: The absolute path of understand database.
    :return: None
    """
    assert os.path.isfile(udb_path)
    assert os.path.isdir(und_path)
    if project_dir is None:
        project_dir = os.path.dirname(os.path.normpath(udb_path))

    process = subprocess.Popen(
        ['und', 'analyze', '-all', udb_path],
        cwd=und_path
    )
    process.wait()


# =======================================================================
class FindUsagesListener(JavaParserLabeledListener):
    def __init__(
            self, common_token_stream: CommonTokenStream = None,
            source_class: str = None, new_class: str = None,
            moved_fields=None, moved_methods=None,
            output_path: str = ""):

        if moved_methods is None:
            self.moved_methods = []
        else:
            self.moved_methods = moved_methods

        if moved_fields is None:
            self.moved_fields = []
        else:
            self.moved_fields = moved_fields

        if common_token_stream is None:
            raise ValueError('common_token_stream is None')
        else:
            self.token_stream_rewriter = TokenStreamRewriter(common_token_stream)

        if source_class is None:
            raise ValueError("source_class is None")
        else:
            self.source_class = source_class

        if new_class is None:
            raise ValueError("new_class is None")
        else:
            self.new_class = new_class

        self.output_path = output_path

        self.is_source_class = False
        self.detected_field = None
        self.detected_method = None
        self.TAB = "\t"
        self.NEW_LINE = "\n"
        self.code = ""


# =======================================================================


class ExtractSubclassAPI:
    def __init__(self, project_dir, file_path, source_class, new_class, moved_fields, moved_methods,
                 new_file_path=None):
        self.project_dir = project_dir
        self.file_path = file_path
        self.new_file_path = new_file_path or "/home/ali/Documents/dev/CodART/input.refactored.java"
        self.source_class = source_class
        self.new_class = new_class
        self.moved_fields = moved_fields
        self.moved_methods = moved_methods
        self.stream = FileStream(self.file_path, encoding="utf8")
        self.lexer = JavaLexer(self.stream)
        self.token_stream = CommonTokenStream(self.lexer)
        self.parser = JavaParserLabeled(self.token_stream)
        self.tree = self.parser.compilationUnit()
        self.walker = ParseTreeWalker()
        self.checked = False

    def extract_subclass(self):
        # udb_path = "/home/ali/Desktop/code/TestProject/TestProject.udb"
        # udb_path=create_understand_database("C:\\Users\\asus\\Desktop\\test_project")
        # source_class = "GodClass"
        # moved_methods = ['method1', 'method3', ]
        # moved_fields = ['field1', 'field2', ]
        udb_path = "C:\\Users\\asus\\Desktop\\test_project\\test_project.udb"
        source_class = "CDL"
        moved_methods = ['getValue', 'rowToJSONArray', 'getVal', ]
        moved_fields = ['number', 'number_2', 'number_1', ]

        # initialize with understand
        father_path_file = ""
        file_list_to_be_propagate = set()
        propagate_classes = set()

        db = und.open(udb_path)
        # db=open(udb_path)

        for cls in db.ents("class"):
            if (cls.simplename() == source_class):
                father_path_file = cls.parent().longname()
                for ref in cls.refs("Coupleby"):
                    # print(ref.ent().longname())
                    propagate_classes.add(ref.ent().longname())
                    # print(ref.ent().parent().relname())
                    # file_list_to_be_propagate.add(ref.ent().parent().relname())
            # if(cls.longname()==fatherclass):
            #     print(cls.parent().relname())
            #     father_path_file=cls.parent().relname()

        father_path_file = "C:\\Users\\asus\\Desktop\\test_project\\CDL.java"
        father_path_directory = "C:\\Users\\asus\\Desktop\\test_project"

        stream = FileStream(father_path_file, encoding='utf8')
        lexer = JavaLexer(stream)
        token_stream = CommonTokenStream(lexer)
        parser = JavaParserLabeled(token_stream)
        parser.getTokenStream()
        parse_tree = parser.compilationUnit()
        my_listener = ExtractSubClassRefactoringListener(common_token_stream=token_stream,
                                                         source_class=source_class,
                                                         new_class=source_class + "extracted",
                                                         moved_fields=moved_fields, moved_methods=moved_methods,
                                                         output_path=father_path_directory)
        walker = ParseTreeWalker()
        walker.walk(t=parse_tree, listener=my_listener)

        with open(father_path_file, mode='w', newline='') as f:
            f.write(my_listener.token_stream_rewriter.getDefaultText())

    # def propagate_refactor(self):


def main():
    """
    it builds the parse tree and walk its corresponding walker so that our overridden methods run.
    """

    # udb_path = "/home/ali/Desktop/code/TestProject/TestProject.udb"
    # udb_path=create_understand_database("C:\\Users\\asus\\Desktop\\test_project")
    # source_class = "GodClass"
    # moved_methods = ['method1', 'method3', ]
    # moved_fields = ['field1', 'field2', ]
    udb_path = "C:\\Users\\asus\\Desktop\\test_project\\test_project.udb"
    source_class = "CDL"
    moved_methods = ['getValue', 'rowToJSONArray', 'getVal', ]
    moved_fields = ['number_2', 'number_1', ]

    # initialize with understand
    father_path_file = ""
    file_list_to_be_propagate = set()
    propagate_classes = set()

    db = und.open(udb_path)
    # db=open(udb_path)

    for cls in db.ents("class"):
        if (cls.simplename() == source_class):
            father_path_file = cls.parent().longname()
            for ref in cls.refs("Coupleby"):
                propagate_classes.add(ref.ent().longname())

    father_path_file = "C:\\Users\\asus\\Desktop\\test_project\\CDL.java"
    father_path_directory = "C:\\Users\\asus\\Desktop\\test_project"

    stream = FileStream(father_path_file, encoding='utf8')
    lexer = JavaLexer(stream)
    token_stream = CommonTokenStream(lexer)
    parser = JavaParserLabeled(token_stream)
    parser.getTokenStream()
    parse_tree = parser.compilationUnit()
    my_listener = ExtractSubClassRefactoringListener(common_token_stream=token_stream,
                                                     source_class=source_class,
                                                     new_class=source_class + "extracted",
                                                     moved_fields=moved_fields, moved_methods=moved_methods,
                                                     output_path=father_path_directory)
    walker = ParseTreeWalker()
    walker.walk(t=parse_tree, listener=my_listener)

    with open(father_path_file, mode='w', newline='') as f:
        f.write(my_listener.token_stream_rewriter.getDefaultText())

    # ================================================================================

    # find_usages_listener = FindUsagesListener()


if __name__ == '__main__':
    main()
