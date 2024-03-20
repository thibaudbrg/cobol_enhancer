import pytest

from ubp_cobol.common import GraphState
from ubp_cobol.generation import critic_generation, new_generation
from ubp_cobol.processing import process_next_file, extender
from ubp_cobol.response_handlers import message_type_decider
from ubp_cobol.utils import print_code_comparator, sanitize_output

from pydantic import BaseModel, Field


@pytest.fixture
def state_process_file(tmp_path) -> GraphState:
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "test.cob"
    p.write_text("""
000010 IDENTIFICATION DIVISION.
000020 PROGRAM-ID. ABORT.
000030 AUTHOR.     TCS.
000040 DATE-COMPLIED.24/05/06.
************************************************************************
000060*     ISSUES AN ABEND AND STOPS THE RUN BY CALLING "CANCEL"
************************************************************************
000080 ENVIRONMENT DIVISION.
TOFANN CONFIGURATION SECTION.
TOFANN SOURCE-COMPUTER. IBM-390.
TOFANN OBJECT-COMPUTER.
TOFANN     PROGRAM COLLATING SEQUENCE EBC.
TOFANN SPECIAL-NAMES.
TOFANN     ALPHABET EBC IS EBCDIC.
************************************************************************
000160*     CONVERTED FROM ASSEMBLER ROUTINE ABORT
************************************************************************
000180 DATA DIVISION.
000190 WORKING-STORAGE SECTION.
000200 PROCEDURE DIVISION.
000210     CALL 'CANCEL'
000220     GOBACK.
""")
    return GraphState(
        files_to_process=[str(p)],
        file_metadata={str(p): {"dependencies": []}},
        metadata={"dependencies": []},
        filename="test.cob",
        critic={},
        old_code=p.read_text(),
        previous_last_gen_code="",
        new_code="",
        specific_demands="",
        copybooks={},
        atlas_answer="",
        atlas_message_type=""
    )


def test_process_file(state_process_file):
    # Specify the test prompt directly for testing purposes
    test_prompt = """
You are a highly precise and proficient AI with expertise in programming and code optimization, specifically with COBOL code. Your task is to scrutinize the provided COBOL code, aiming to refactor it into the most efficient and error-free version possible. Focus on eliminating redundancy, optimizing the logic flow, correcting any errors, bad practices found or old practices (e.g. replace GO TO for PERFORM). It is crucial that the improvements maintain or enhance the original functionality of the code. 
- Don't remove CONFIGURATION_SECTION,
- Don't remove existing comments,
- If you feel it necessary, add comments,
- The existing comments should not be removed,

It's crucial to preserve the original line numbers on the left side of each line of code. These line numbers are essential for tracking and documentation purposes. Please make sure that any modifications you suggest do not remove or alter these line numbers.

It's crucial that you don't remove existing comments. Even more important, it is crucial that you add more comments for a better understanding.

Please return only the improved COBOL code, with no additional comments or explanations. It's crucial to wrap the code into the markdown notation ```cobol [the_code] ````


Here are the useful infos (metadatas) of the provided file:
{metadata}

Here are the Copybooks used in the file: 
{copybooks}

And here is the COBOL file named {filename}:

{old_code}
"""

    updated_state = process_next_file(state_process_file, template=test_prompt)

    # Verify that the new code is set as expected
    assert "new_code" in updated_state
    comparison_output = print_code_comparator(state_process_file["old_code"],
                                              sanitize_output(updated_state["new_code"]))

    print(comparison_output)


@pytest.fixture
def state_critic_gen(tmp_path) -> GraphState:
    d = tmp_path / "new_gen"
    d.mkdir()
    p = d / "new_test.cob"
    p.write_text("""
    000010 IDENTIFICATION DIVISION.                                                 
    000020 PROGRAM-ID. READCARD.                                                    
    000030 AUTHOR.TATA CONSULTANCY SERVICES.                                        
    000040 DATE-COMPILED.FEB 2006.                                                  
    ************************************************************************        
    000060*THIS PROGRAM READS THE INSTREAM DATA AND WRITES TO SYSOUT.               
    ************************************************************************        
    000080 ENVIRONMENT DIVISION.                                                    
    ************************************************************************
    000100*THE FOLLOWING LINES OF CODE  COMMENTED AS THIS IS NOT REQUIRED BY   
    000110*THE PROGRAM FUNCTIONALITY.
    ************************************************************************
    TOFAN8*CONFIGURATION SECTION.
    TOFAN8*SOURCE-COMPUTER. IBM-390.
    TOFAN8*OBJECT-COMPUTER.
    TOFAN8*    PROGRAM COLLATING SEQUENCE EBC.
    TOFAN8*SPECIAL-NAMES.
    TOFAN8*    ALPHABET EBC IS EBCDIC.
    000190 INPUT-OUTPUT SECTION.                                                    
    000200 FILE-CONTROL.                                                            
    000210     SELECT CARD ASSIGN TO CARDIN                                         
    000220     ORGANIZATION IS LINE SEQUENTIAL                                      
    000230     ACCESS IS SEQUENTIAL                                                 
    000240     FILE STATUS IS F-KEY1.                                               
    000250                                                                          
    000260     SELECT COUT ASSIGN TO  READOUT                                       
    000270     ORGANIZATION IS LINE SEQUENTIAL                                      
    000280     ACCESS IS SEQUENTIAL                                                 
    000290     FILE STATUS IS F-KEY2.                                               
    000300                                                                          
    000310 DATA DIVISION.                                                           
    000320 FILE SECTION.                                                            
    000330 FD COUT.                                                                 
    000340 01 OUT-REC          PIC X(133).                                          
    000350                                                                          
    000360 FD CARD.                                                                 
    000370 01 INP-REC          PIC X(80).                                           
    000380 WORKING-STORAGE SECTION.                                                 
    000390 77  CMS-IDENTIFICATION PIC X(8) VALUE 'WEADCARD'.                        
    000400 77  CMS-ID-VALUE PIC X(44)   VALUE                                       
    000410         'CMS-ID=17/02/06/15:58:32/GWDR/TOFRS8  /V0   '.                  
    000420 77  WS-OPEN-FLAG      PIC X(1) VALUE IS 'N'.                             
    ************************************************************************        
    000440*         RECORD FORMAT IN THE OUTPUT FILE                                
    ************************************************************************        
    000460                                                                          
    000470 01  LINE1.                                                               
    000480     05  FILLER        PIC X(48) VALUE IS                                 
    000490-       '****************** DEBUT DES CARTES PARAMETRES '.                
    000500     05  FILLER       PIC X(32) VALUE IS ALL '*'.                         
    000510     05  FILLER       PIC X(53) VALUE IS SPACES.                          
    000520 01  LINE2.                                                               
    000530     05  FILLER        PIC X(40) VALUE IS                                 
    000540-       '1...5...10....5...20....5...30....5...40'.                       
    000550     05  FILLER        PIC X(40) VALUE IS                                 
    000560-       '....5...50....5...60....5...70....5...80'.                       
    000570     05  FILLER       PIC X(53) VALUE IS SPACES.                          
    000580 01  LINE3.                                                               
    000590     05  FILLER        PIC X(46) VALUE IS                                 
    000600-       '****************** FIN DES CARTES PARAMETRES '.                  
    000610     05  FILLER       PIC X(34) VALUE IS ALL '*'.                         
    000620     05  FILLER       PIC X(53) VALUE IS SPACES.                          
    000630 01  PARAMETER-LINE.                                                      
    000640     05  PARAMETERS    PIC X(80).                                         
    000650     05  FILLER       PIC X(53) VALUE IS SPACES.                          
    000660 77  F-KEY1     PIC X(2).                                                 
    000670 77  F-KEY2     PIC X(2).                                                 
    000680 LINKAGE SECTION.                                                         
    000690  01  LK-CARTE  PIC X(80).                                                
    000700 PROCEDURE DIVISION USING LK-CARTE.                                       
    000710 MAIN-PARA.                                                               
    ************************************************************************        
    000730*         CHECKS IF THE FILE IS OPEN                                      
    ************************************************************************        
    000750      IF WS-OPEN-FLAG = 'Y'                                               
    000760          GO TO READ-PARA                                                 
    000770      END-IF.                                                             
    ************************************************************************        
    000790*     ALLOCATES READOUT TO SYSOUT USING BPXWDYN                           
    ************************************************************************        
    000810      OPEN INPUT CARD.                                                    
    000820      MOVE 'Y' TO WS-OPEN-FLAG.                                           
    000830      OPEN OUTPUT COUT.                                                   
    000840      PERFORM INIT-PARA.                                                  
    000850      PERFORM READ-PARA.                                                  
    000860 INIT-PARA.                                                               
    ************************************************************************        
    000880*         WRITES FIRST AND SECOND LINE TO SYSOUT                          
    ************************************************************************        
    000900      WRITE OUT-REC FROM LINE1                                            
    000910      WRITE OUT-REC FROM LINE2.                                           
    000920 READ-PARA.                                                               
    ************************************************************************        
    000940*         READS INSTREAM DATA AND WRITES TO SYSOUT                        
    ************************************************************************        
    000960      READ CARD INTO PARAMETERS AT END GO TO CLOSE-PARA.                  
    000970      MOVE PARAMETERS TO  LK-CARTE.                            
    000980      WRITE OUT-REC FROM PARAMETER-LINE                                
    000990      PERFORM GOBACK-PARA.                                                
    001000 CLOSE-PARA.                                                              
    ************************************************************************        
    001020*         WRITES LAST LINE  TO SYSOUT                                     
    ************************************************************************        
    001040      MOVE '/*' TO LK-CARTE                                               
    001050      WRITE OUT-REC FROM LINE3.                                           
    001060      CLOSE CARD.                                                         
    001070      CLOSE COUT.                                                         
    001080 GOBACK-PARA.                                                             
    001090      GOBACK.                                                             
    """)
    return GraphState(
        files_to_process=[str(p)],
        file_metadata={str(p): {"dependencies": []}},
        metadata={"dependencies": []},
        filename="new_test.cob",
        critic={},
        old_code=p.read_text(),
        previous_last_gen_code="",
        new_code="""
        000010 IDENTIFICATION DIVISION.                                                 
        000020 PROGRAM-ID. READCARD.                                                    
        000030 AUTHOR.TATA CONSULTANCY SERVICES.                                        
        000040 DATE-COMPILED.FEB 2006.                                                  
        ************************************************************************        
        000060*THIS PROGRAM READS THE INSTREAM DATA AND WRITES TO SYSOUT.               
        ************************************************************************        
        000080 ENVIRONMENT DIVISION.                                                    
        ************************************************************************
        000100*THE FOLLOWING LINES OF CODE  COMMENTED AS THIS IS NOT REQUIRED BY   
        000110*THE PROGRAM FUNCTIONALITY.
        ************************************************************************
        TOFAN8*CONFIGURATION SECTION.
        TOFAN8*SOURCE-COMPUTER. IBM-390.
        TOFAN8*OBJECT-COMPUTER.
        TOFAN8*    PROGRAM COLLATING SEQUENCE EBC.
        TOFAN8*SPECIAL-NAMES.
        TOFAN8*    ALPHABET EBC IS EBCDIC.
        000190 INPUT-OUTPUT SECTION.                                                    
        000200 FILE-CONTROL.                                                            
        000210     SELECT CARD ASSIGN TO CARDIN                                         
        000220     ORGANIZATION IS LINE SEQUENTIAL                                      
        000230     ACCESS IS SEQUENTIAL                                                 
        000240     FILE STATUS IS F-KEY1.                                               
        000250                                                                          
        000260     SELECT COUT ASSIGN TO  READOUT                                       
        000270     ORGANIZATION IS LINE SEQUENTIAL                                      
        000280     ACCESS IS SEQUENTIAL                                                 
        000290     FILE STATUS IS F-KEY2.                                               
        000300                                                                          
        000310 DATA DIVISION.                                                           
        000320 FILE SECTION.                                                            
        000330 FD COUT.                                                                 
        000340 01 OUT-REC          PIC X(133).                                          
        000350                                                                          
        000360 FD CARD.                                                                 
        000370 01 INP-REC          PIC X(80).                                           
        000380 WORKING-STORAGE SECTION.                                                 
        000390 77  CMS-IDENTIFICATION PIC X(8) VALUE 'WEADCARD'.                        
        000400 77  CMS-ID-VALUE PIC X(44)   VALUE                                       
        000410         'CMS-ID=17/02/06/15:58:32/GWDR/TOFRS8  /V0   '.                  
        000420 77  WS-OPEN-FLAG      PIC X(1) VALUE IS 'N'.                             
        ************************************************************************        
        000440*         RECORD FORMAT IN THE OUTPUT FILE                                
        ************************************************************************        
        000460                                                                          
        000470 01  LINE1.                                                               
        000480     05  FILLER        PIC X(48) VALUE IS                                 
        000490-       '****************** DEBUT DES CARTES PARAMETRES '.                
        000500     05  FILLER       PIC X(32) VALUE IS ALL '*'.                         
        000510     05  FILLER       PIC X(53) VALUE IS SPACES.                          
        000520 01  LINE2.                                                               
        000530     05  FILLER        PIC X(40) VALUE IS                                 
        000540-       '1...5...10....5...20....5...30....5...40'.                       
        000550     05  FILLER        PIC X(40) VALUE IS                                 
        000560-       '....5...50....5...60....5...70....5...80'.                       
        000570     05  FILLER       PIC X(53) VALUE IS SPACES.                          
        000580 01  LINE3.                                                               
        000590     05  FILLER        PIC X(46) VALUE IS                                 
        000600-       '****************** FIN DES CARTES PARAMETRES '.                  
        000610     05  FILLER       PIC X(34) VALUE IS ALL '*'.                         
        000620     05  FILLER       PIC X(53) VALUE IS SPACES.                          
        000630 01  PARAMETER-LINE.                                                      
        000640     05  PARAMETERS    PIC X(80).                                         
        000650     05  FILLER       PIC X(53) VALUE IS SPACES.                          
        000660 77  F-KEY1     PIC X(2).                                                 
        000670 77  F-KEY2     PIC X(2).                                                 
        000680 LINKAGE SECTION.                                                         
        000690  01  LK-CARTE  PIC X(80).                                                
        000700 PROCEDURE DIVISION USING LK-CARTE.                                       
        000710 MAIN-PARA.                                                               
        ************************************************************************        
        000730*         CHECKS IF THE FILE IS OPEN                                      
        ************************************************************************        
        000750      IF WS-OPEN-FLAG NOT = 'Y'                                           
        000760          PERFORM INITIALIZE-FILES                                        
        000770      END-IF.                                                             
        000790      PERFORM PROCESS-FILES UNTIL WS-OPEN-FLAG = 'N'.                     
        000800      STOP RUN.                                                           
        000810 INITIALIZE-FILES.                                                        
        000820      OPEN INPUT CARD.                                                    
        000830      MOVE 'Y' TO WS-OPEN-FLAG.                                           
        000840      OPEN OUTPUT COUT.                                                   
        000850      WRITE OUT-REC FROM LINE1                                            
        000860      WRITE OUT-REC FROM LINE2.                                           
        000870 PROCESS-FILES.                                                           
        000880      READ CARD INTO PARAMETERS AT END SET WS-OPEN-FLAG TO 'N'.           
        000890      MOVE PARAMETERS TO LK-CARTE.                                        
        000900      WRITE OUT-REC FROM PARAMETER-LINE.                                  
        000910      IF WS-OPEN-FLAG = 'N'                                               
        000920          PERFORM TERMINATE-FILES                                         
        000930      END-IF.                                                             
        000940 TERMINATE-FILES.                                                         
        000950      MOVE '/*' TO LK-CARTE                                               
        000960      WRITE OUT-REC FROM LINE3.                                           
        000970      CLOSE CARD.                                                         
        000980      CLOSE COUT.
        """,
        specific_demands="",
        copybooks={},
        atlas_answer="",
        atlas_message_type=""
    )


def test_critic_gen(state_critic_gen):
    # Specify the test prompt directly for testing purposes
    test_prompt = """
You are an expert in code analysis with a specific focus on COBOL. Your current task is to compare two/three versions of COBOL code: the original version, the previous last generated version (optional) and the new generated, optimized version. Please scrutinize the two/three versions carefully. Your goal is to identify any relevant errors introduced in the new code or discrepancies that could lead to potential issues. For each error or significant discrepancy you find, please:

Clearly cite the issue.
Provide a detailed explanation of why it is problematic.
Offer explicit steps that should be taken to resolve it.
It's important to note that you should not implement these solutions directly; rather, your output should be a clear and concise explanation of the errors found and guidance on how to address them. This will aid developers in understanding and applying the necessary corrections themselves.

If there is below a "previous last" version of the code provided and a "previous critic" then create a new critic as explained above but emphasize on the previous critics and check if they are now resolved.

If you don't find any relevant issue, then state it explicitly.
You are permissive.

Below are the two/three versions of the COBOL code for your comparison:

===========================================

Original COBOL Code:

{old_code}


===========================================
Previous critic (optional):
{specific_demands}

{previous_critic}

================

Previous Last Generated COBOL Code (optional):

{previous_last_gen_code}


===========================================

Newly Generated COBOL Code:

{new_code}

"""

    updated_state = critic_generation(state_critic_gen, template=test_prompt)

    # assert updated_state["critic"].description is not None
    # assert updated_state["critic"].grade in ["good", "bad"]


@pytest.fixture
def state_new_gen_with_atlas_answer(tmp_path) -> GraphState:
    class CodeReviewResult(BaseModel):
        description: str = Field(description="A detailed description of the code review.")
        grade: str = Field(description="The grade of the code review, e.g., 'good' or 'bad'.")

    d = tmp_path / "new_gen"
    d.mkdir()
    p = d / "new_test.cob"
    p.write_text("""
000010 IDENTIFICATION DIVISION.                                                 
000020 PROGRAM-ID. READCARD.                                                    
000030 AUTHOR.TATA CONSULTANCY SERVICES.                                        
000040 DATE-COMPILED.FEB 2006.                                                  
************************************************************************        
000060*THIS PROGRAM READS THE INSTREAM DATA AND WRITES TO SYSOUT.               
************************************************************************        
000080 ENVIRONMENT DIVISION.                                                    
************************************************************************
000100*THE FOLLOWING LINES OF CODE  COMMENTED AS THIS IS NOT REQUIRED BY   
000110*THE PROGRAM FUNCTIONALITY.
************************************************************************
TOFAN8*CONFIGURATION SECTION.
TOFAN8*SOURCE-COMPUTER. IBM-390.
TOFAN8*OBJECT-COMPUTER.
TOFAN8*    PROGRAM COLLATING SEQUENCE EBC.
TOFAN8*SPECIAL-NAMES.
TOFAN8*    ALPHABET EBC IS EBCDIC.
000190 INPUT-OUTPUT SECTION.                                                    
000200 FILE-CONTROL.                                                            
000210     SELECT CARD ASSIGN TO CARDIN                                         
000220     ORGANIZATION IS LINE SEQUENTIAL                                      
000230     ACCESS IS SEQUENTIAL                                                 
000240     FILE STATUS IS F-KEY1.                                               
000250                                                                          
000260     SELECT COUT ASSIGN TO  READOUT                                       
000270     ORGANIZATION IS LINE SEQUENTIAL                                      
000280     ACCESS IS SEQUENTIAL                                                 
000290     FILE STATUS IS F-KEY2.                                               
000300                                                                          
000310 DATA DIVISION.                                                           
000320 FILE SECTION.                                                            
000330 FD COUT.                                                                 
000340 01 OUT-REC          PIC X(133).                                          
000350                                                                          
000360 FD CARD.                                                                 
000370 01 INP-REC          PIC X(80).                                           
000380 WORKING-STORAGE SECTION.                                                 
000390 77  CMS-IDENTIFICATION PIC X(8) VALUE 'WEADCARD'.                        
000400 77  CMS-ID-VALUE PIC X(44)   VALUE                                       
000410         'CMS-ID=17/02/06/15:58:32/GWDR/TOFRS8  /V0   '.                  
000420 77  WS-OPEN-FLAG      PIC X(1) VALUE IS 'N'.                             
************************************************************************        
000440*         RECORD FORMAT IN THE OUTPUT FILE                                
************************************************************************        
000460                                                                          
000470 01  LINE1.                                                               
000480     05  FILLER        PIC X(48) VALUE IS                                 
000490-       '****************** DEBUT DES CARTES PARAMETRES '.                
000500     05  FILLER       PIC X(32) VALUE IS ALL '*'.                         
000510     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000520 01  LINE2.                                                               
000530     05  FILLER        PIC X(40) VALUE IS                                 
000540-       '1...5...10....5...20....5...30....5...40'.                       
000550     05  FILLER        PIC X(40) VALUE IS                                 
000560-       '....5...50....5...60....5...70....5...80'.                       
000570     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000580 01  LINE3.                                                               
000590     05  FILLER        PIC X(46) VALUE IS                                 
000600-       '****************** FIN DES CARTES PARAMETRES '.                  
000610     05  FILLER       PIC X(34) VALUE IS ALL '*'.                         
000620     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000630 01  PARAMETER-LINE.                                                      
000640     05  PARAMETERS    PIC X(80).                                         
000650     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000660 77  F-KEY1     PIC X(2).                                                 
000670 77  F-KEY2     PIC X(2).                                                 
000680 LINKAGE SECTION.                                                         
000690  01  LK-CARTE  PIC X(80).                                                
000700 PROCEDURE DIVISION USING LK-CARTE.                                       
000710 MAIN-PARA.                                                               
************************************************************************        
000730*         CHECKS IF THE FILE IS OPEN                                      
************************************************************************        
000750      IF WS-OPEN-FLAG = 'Y'                                               
000760          GO TO READ-PARA                                                 
000770      END-IF.                                                             
************************************************************************        
000790*     ALLOCATES READOUT TO SYSOUT USING BPXWDYN                           
************************************************************************        
000810      OPEN INPUT CARD.                                                    
000820      MOVE 'Y' TO WS-OPEN-FLAG.                                           
000830      OPEN OUTPUT COUT.                                                   
000840      PERFORM INIT-PARA.                                                  
000850      PERFORM READ-PARA.                                                  
000860 INIT-PARA.                                                               
************************************************************************        
000880*         WRITES FIRST AND SECOND LINE TO SYSOUT                          
************************************************************************        
000900      WRITE OUT-REC FROM LINE1                                            
000910      WRITE OUT-REC FROM LINE2.                                           
000920 READ-PARA.                                                               
************************************************************************        
000940*         READS INSTREAM DATA AND WRITES TO SYSOUT                        
************************************************************************        
000960      READ CARD INTO PARAMETERS AT END GO TO CLOSE-PARA.                  
000970      MOVE PARAMETERS TO  LK-CARTE.                            
000980      WRITE OUT-REC FROM PARAMETER-LINE                                
000990      PERFORM GOBACK-PARA.                                                
001000 CLOSE-PARA.                                                              
************************************************************************        
001020*         WRITES LAST LINE  TO SYSOUT                                     
************************************************************************        
001040      MOVE '/*' TO LK-CARTE                                               
001050      WRITE OUT-REC FROM LINE3.                                           
001060      CLOSE CARD.                                                         
001070      CLOSE COUT.                                                         
001080 GOBACK-PARA.                                                             
001090      GOBACK.                                                             
""")
    return GraphState(
        files_to_process=[str(p)],
        file_metadata={str(p): {"dependencies": []}},
        metadata={"dependencies": []},
        filename="new_test.cob",
        critic={
            "description": """
Upon comparing the original and the newly generated COBOL code, there are no significant discrepancies or errors introduced in the new code. The changes made in the new version seem to be optimizations and restructuring of the code for better readability and maintainability. Specifically, the introduction of the INITIALIZE-FILES, PROCESS-FILES, and TERMINATE-FILES paragraphs in the new code makes the program's flow more understandable. The change from checking if the file is open with 'IF WS-OPEN-FLAG = 'Y'' to 'IF WS-OPEN-FLAG NOT = 'Y'' and the subsequent restructuring of the file processing logic are logical and do not introduce any functional discrepancies. The use of 'PERFORM ... UNTIL WS-OPEN-FLAG = 'N'' for looping through the file processing also seems to be a more structured approach compared to the original code. Overall, the new code maintains the functionality of the original code while improving its structure and readability.
""",
            "grade": "good"
        },
        old_code=p.read_text(),
        previous_last_gen_code="",
        new_code="""
000010 IDENTIFICATION DIVISION.                                                 
000020 PROGRAM-ID. READCARD.                                                    
000030 AUTHOR.TATA CONSULTANCY SERVICES.                                        
000040 DATE-COMPILED.FEB 2006.                                                  
************************************************************************        
000060*THIS PROGRAM READS THE INSTREAM DATA AND WRITES TO SYSOUT.               
************************************************************************        
000080 ENVIRONMENT DIVISION.                                                    
************************************************************************
000100*THE FOLLOWING LINES OF CODE  COMMENTED AS THIS IS NOT REQUIRED BY   
000110*THE PROGRAM FUNCTIONALITY.
************************************************************************
TOFAN8*CONFIGURATION SECTION.
TOFAN8*SOURCE-COMPUTER. IBM-390.
TOFAN8*OBJECT-COMPUTER.
TOFAN8*    PROGRAM COLLATING SEQUENCE EBC.
TOFAN8*SPECIAL-NAMES.
TOFAN8*    ALPHABET EBC IS EBCDIC.
000190 INPUT-OUTPUT SECTION.                                                    
000200 FILE-CONTROL.                                                            
000210     SELECT CARD ASSIGN TO CARDIN                                         
000220     ORGANIZATION IS LINE SEQUENTIAL                                      
000230     ACCESS IS SEQUENTIAL                                                 
000240     FILE STATUS IS F-KEY1.                                               
000250                                                                          
000260     SELECT COUT ASSIGN TO  READOUT                                       
000270     ORGANIZATION IS LINE SEQUENTIAL                                      
000280     ACCESS IS SEQUENTIAL                                                 
000290     FILE STATUS IS F-KEY2.                                               
000300                                                                          
000310 DATA DIVISION.                                                           
000320 FILE SECTION.                                                            
000330 FD COUT.                                                                 
000340 01 OUT-REC          PIC X(133).                                          
000350                                                                          
000360 FD CARD.                                                                 
000370 01 INP-REC          PIC X(80).                                           
000380 WORKING-STORAGE SECTION.                                                 
000390 77  CMS-IDENTIFICATION PIC X(8) VALUE 'WEADCARD'.                        
000400 77  CMS-ID-VALUE PIC X(44)   VALUE                                       
000410         'CMS-ID=17/02/06/15:58:32/GWDR/TOFRS8  /V0   '.                  
000420 77  WS-OPEN-FLAG      PIC X(1) VALUE IS 'N'.                             
************************************************************************        
000440*         RECORD FORMAT IN THE OUTPUT FILE                                
************************************************************************        
000460                                                                          
000470 01  LINE1.                                                               
000480     05  FILLER        PIC X(48) VALUE IS                                 
000490-       '****************** DEBUT DES CARTES PARAMETRES '.                
000500     05  FILLER       PIC X(32) VALUE IS ALL '*'.                         
000510     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000520 01  LINE2.                                                               
000530     05  FILLER        PIC X(40) VALUE IS                                 
000540-       '1...5...10....5...20....5...30....5...40'.                       
000550     05  FILLER        PIC X(40) VALUE IS                                 
000560-       '....5...50....5...60....5...70....5...80'.                       
000570     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000580 01  LINE3.                                                               
000590     05  FILLER        PIC X(46) VALUE IS                                 
000600-       '****************** FIN DES CARTES PARAMETRES '.                  
000610     05  FILLER       PIC X(34) VALUE IS ALL '*'.                         
000620     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000630 01  PARAMETER-LINE.                                                      
000640     05  PARAMETERS    PIC X(80).                                         
000650     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000660 77  F-KEY1     PIC X(2).                                                 
000670 77  F-KEY2     PIC X(2).                                                 
000680 LINKAGE SECTION.                                                         
000690  01  LK-CARTE  PIC X(80).                                                
000700 PROCEDURE DIVISION USING LK-CARTE.                                       
000710 MAIN-PARA.                                                               
************************************************************************        
000730*         CHECKS IF THE FILE IS OPEN                                      
************************************************************************        
000750      IF WS-OPEN-FLAG NOT = 'Y'                                           
000760          PERFORM INITIALIZE-FILES                                        
000770      END-IF.                                                             
000790      PERFORM PROCESS-FILES UNTIL WS-OPEN-FLAG = 'N'.                     
000800      STOP RUN.                                                           
000810 INITIALIZE-FILES.                                                        
000820      OPEN INPUT CARD.                                                    
000830      MOVE 'Y' TO WS-OPEN-FLAG.                                           
000840      OPEN OUTPUT COUT.                                                   
000850      WRITE OUT-REC FROM LINE1                                            
000860      WRITE OUT-REC FROM LINE2.                                           
000870 PROCESS-FILES.                                                           
000880      READ CARD INTO PARAMETERS AT END SET WS-OPEN-FLAG TO 'N'.           
000890      MOVE PARAMETERS TO LK-CARTE.                                        
000900      WRITE OUT-REC FROM PARAMETER-LINE.                                  
000910      IF WS-OPEN-FLAG = 'N'                                               
000920          PERFORM TERMINATE-FILES                                         
000930      END-IF.                                                             
000940 TERMINATE-FILES.                                                         
000950      MOVE '/*' TO LK-CARTE                                               
000960      WRITE OUT-REC FROM LINE3.                                           
000970      CLOSE CARD.                                                         
000980      CLOSE COUT.
""",
        specific_demands="change close cout for go back",
        copybooks={},
        atlas_answer="""
Error(002): Program 'XYZ' compilation halted - SYNTAX ERROR at line 104
Error(015): Missing END-IF statement in 'CALC-TOTAL' section at line 216
Warning(007): Implicit declaration of variable 'TOTAL-COST' at line 150
Error(034): 'PERFORM' loop starting at line 178 cannot reach termination condition
Error(045): Incompatible types for operation '>' in 'CHECK-DISCOUNT' procedure at line 320
Warning(011): Deprecated usage of 'COMPUTE' statement at line 89
Error(067): Array index out of bounds in 'ITEM-LIST' at line 462
Error(081): Division by zero possibility in 'DIVIDE-TOTALS' at line 501
Warning(021): Variable 'CUST-ID' is not used within its scope at line 233
Error(099): Incorrect number of parameters passed to 'UPDATE-RECORD' at line 298
""",
        atlas_message_type="execution_error"
    )


def test_new_gen_with_atlas_answer(state_new_gen_with_atlas_answer):
    updated_state = new_generation(state_new_gen_with_atlas_answer)

    # Verify that the new code is as expected
    assert "new_code" in updated_state
    assert "previous_last_gen_code" in updated_state
    # comparison_output = print_code_comparator(state_new_gen_with_human_feedback["old_code"],
    #                                           sanitize_output(updated_state["new_code"]))

    # Print comparison output for inspection
    # print(comparison_output)


@pytest.fixture
def state_new_gen_with_human_feedback(tmp_path) -> GraphState:
    class CodeReviewResult(BaseModel):
        description: str = Field(description="A detailed description of the code review.")
        grade: str = Field(description="The grade of the code review, e.g., 'good' or 'bad'.")

    d = tmp_path / "new_gen"
    d.mkdir()
    p = d / "new_test.cob"
    p.write_text("""
000010 IDENTIFICATION DIVISION.                                                 
000020 PROGRAM-ID. READCARD.                                                    
000030 AUTHOR.TATA CONSULTANCY SERVICES.                                        
000040 DATE-COMPILED.FEB 2006.                                                  
************************************************************************        
000060*THIS PROGRAM READS THE INSTREAM DATA AND WRITES TO SYSOUT.               
************************************************************************        
000080 ENVIRONMENT DIVISION.                                                    
************************************************************************
000100*THE FOLLOWING LINES OF CODE  COMMENTED AS THIS IS NOT REQUIRED BY   
000110*THE PROGRAM FUNCTIONALITY.
************************************************************************
TOFAN8*CONFIGURATION SECTION.
TOFAN8*SOURCE-COMPUTER. IBM-390.
TOFAN8*OBJECT-COMPUTER.
TOFAN8*    PROGRAM COLLATING SEQUENCE EBC.
TOFAN8*SPECIAL-NAMES.
TOFAN8*    ALPHABET EBC IS EBCDIC.
000190 INPUT-OUTPUT SECTION.                                                    
000200 FILE-CONTROL.                                                            
000210     SELECT CARD ASSIGN TO CARDIN                                         
000220     ORGANIZATION IS LINE SEQUENTIAL                                      
000230     ACCESS IS SEQUENTIAL                                                 
000240     FILE STATUS IS F-KEY1.                                               
000250                                                                          
000260     SELECT COUT ASSIGN TO  READOUT                                       
000270     ORGANIZATION IS LINE SEQUENTIAL                                      
000280     ACCESS IS SEQUENTIAL                                                 
000290     FILE STATUS IS F-KEY2.                                               
000300                                                                          
000310 DATA DIVISION.                                                           
000320 FILE SECTION.                                                            
000330 FD COUT.                                                                 
000340 01 OUT-REC          PIC X(133).                                          
000350                                                                          
000360 FD CARD.                                                                 
000370 01 INP-REC          PIC X(80).                                           
000380 WORKING-STORAGE SECTION.                                                 
000390 77  CMS-IDENTIFICATION PIC X(8) VALUE 'WEADCARD'.                        
000400 77  CMS-ID-VALUE PIC X(44)   VALUE                                       
000410         'CMS-ID=17/02/06/15:58:32/GWDR/TOFRS8  /V0   '.                  
000420 77  WS-OPEN-FLAG      PIC X(1) VALUE IS 'N'.                             
************************************************************************        
000440*         RECORD FORMAT IN THE OUTPUT FILE                                
************************************************************************        
000460                                                                          
000470 01  LINE1.                                                               
000480     05  FILLER        PIC X(48) VALUE IS                                 
000490-       '****************** DEBUT DES CARTES PARAMETRES '.                
000500     05  FILLER       PIC X(32) VALUE IS ALL '*'.                         
000510     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000520 01  LINE2.                                                               
000530     05  FILLER        PIC X(40) VALUE IS                                 
000540-       '1...5...10....5...20....5...30....5...40'.                       
000550     05  FILLER        PIC X(40) VALUE IS                                 
000560-       '....5...50....5...60....5...70....5...80'.                       
000570     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000580 01  LINE3.                                                               
000590     05  FILLER        PIC X(46) VALUE IS                                 
000600-       '****************** FIN DES CARTES PARAMETRES '.                  
000610     05  FILLER       PIC X(34) VALUE IS ALL '*'.                         
000620     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000630 01  PARAMETER-LINE.                                                      
000640     05  PARAMETERS    PIC X(80).                                         
000650     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000660 77  F-KEY1     PIC X(2).                                                 
000670 77  F-KEY2     PIC X(2).                                                 
000680 LINKAGE SECTION.                                                         
000690  01  LK-CARTE  PIC X(80).                                                
000700 PROCEDURE DIVISION USING LK-CARTE.                                       
000710 MAIN-PARA.                                                               
************************************************************************        
000730*         CHECKS IF THE FILE IS OPEN                                      
************************************************************************        
000750      IF WS-OPEN-FLAG = 'Y'                                               
000760          GO TO READ-PARA                                                 
000770      END-IF.                                                             
************************************************************************        
000790*     ALLOCATES READOUT TO SYSOUT USING BPXWDYN                           
************************************************************************        
000810      OPEN INPUT CARD.                                                    
000820      MOVE 'Y' TO WS-OPEN-FLAG.                                           
000830      OPEN OUTPUT COUT.                                                   
000840      PERFORM INIT-PARA.                                                  
000850      PERFORM READ-PARA.                                                  
000860 INIT-PARA.                                                               
************************************************************************        
000880*         WRITES FIRST AND SECOND LINE TO SYSOUT                          
************************************************************************        
000900      WRITE OUT-REC FROM LINE1                                            
000910      WRITE OUT-REC FROM LINE2.                                           
000920 READ-PARA.                                                               
************************************************************************        
000940*         READS INSTREAM DATA AND WRITES TO SYSOUT                        
************************************************************************        
000960      READ CARD INTO PARAMETERS AT END GO TO CLOSE-PARA.                  
000970      MOVE PARAMETERS TO  LK-CARTE.                            
000980      WRITE OUT-REC FROM PARAMETER-LINE                                
000990      PERFORM GOBACK-PARA.                                                
001000 CLOSE-PARA.                                                              
************************************************************************        
001020*         WRITES LAST LINE  TO SYSOUT                                     
************************************************************************        
001040      MOVE '/*' TO LK-CARTE                                               
001050      WRITE OUT-REC FROM LINE3.                                           
001060      CLOSE CARD.                                                         
001070      CLOSE COUT.                                                         
001080 GOBACK-PARA.                                                             
001090      GOBACK.                                                             
""")
    return GraphState(
        files_to_process=[str(p)],
        file_metadata={str(p): {"dependencies": []}},
        metadata={"dependencies": []},
        filename="new_test.cob",
        critic={
            "description": """
Upon comparing the original and the newly generated COBOL code, there are no significant discrepancies or errors introduced in the new code. The changes made in the new version seem to be optimizations and restructuring of the code for better readability and maintainability. Specifically, the introduction of the INITIALIZE-FILES, PROCESS-FILES, and TERMINATE-FILES paragraphs in the new code makes the program's flow more understandable. The change from checking if the file is open with 'IF WS-OPEN-FLAG = 'Y'' to 'IF WS-OPEN-FLAG NOT = 'Y'' and the subsequent restructuring of the file processing logic are logical and do not introduce any functional discrepancies. The use of 'PERFORM ... UNTIL WS-OPEN-FLAG = 'N'' for looping through the file processing also seems to be a more structured approach compared to the original code. Overall, the new code maintains the functionality of the original code while improving its structure and readability.
""",
            "grade": "good"
        },
        old_code=p.read_text(),
        previous_last_gen_code="",
        new_code="""
000010 IDENTIFICATION DIVISION.                                                 
000020 PROGRAM-ID. READCARD.                                                    
000030 AUTHOR.TATA CONSULTANCY SERVICES.                                        
000040 DATE-COMPILED.FEB 2006.                                                  
************************************************************************        
000060*THIS PROGRAM READS THE INSTREAM DATA AND WRITES TO SYSOUT.               
************************************************************************        
000080 ENVIRONMENT DIVISION.                                                    
************************************************************************
000100*THE FOLLOWING LINES OF CODE  COMMENTED AS THIS IS NOT REQUIRED BY   
000110*THE PROGRAM FUNCTIONALITY.
************************************************************************
TOFAN8*CONFIGURATION SECTION.
TOFAN8*SOURCE-COMPUTER. IBM-390.
TOFAN8*OBJECT-COMPUTER.
TOFAN8*    PROGRAM COLLATING SEQUENCE EBC.
TOFAN8*SPECIAL-NAMES.
TOFAN8*    ALPHABET EBC IS EBCDIC.
000190 INPUT-OUTPUT SECTION.                                                    
000200 FILE-CONTROL.                                                            
000210     SELECT CARD ASSIGN TO CARDIN                                         
000220     ORGANIZATION IS LINE SEQUENTIAL                                      
000230     ACCESS IS SEQUENTIAL                                                 
000240     FILE STATUS IS F-KEY1.                                               
000250                                                                          
000260     SELECT COUT ASSIGN TO  READOUT                                       
000270     ORGANIZATION IS LINE SEQUENTIAL                                      
000280     ACCESS IS SEQUENTIAL                                                 
000290     FILE STATUS IS F-KEY2.                                               
000300                                                                          
000310 DATA DIVISION.                                                           
000320 FILE SECTION.                                                            
000330 FD COUT.                                                                 
000340 01 OUT-REC          PIC X(133).                                          
000350                                                                          
000360 FD CARD.                                                                 
000370 01 INP-REC          PIC X(80).                                           
000380 WORKING-STORAGE SECTION.                                                 
000390 77  CMS-IDENTIFICATION PIC X(8) VALUE 'WEADCARD'.                        
000400 77  CMS-ID-VALUE PIC X(44)   VALUE                                       
000410         'CMS-ID=17/02/06/15:58:32/GWDR/TOFRS8  /V0   '.                  
000420 77  WS-OPEN-FLAG      PIC X(1) VALUE IS 'N'.                             
************************************************************************        
000440*         RECORD FORMAT IN THE OUTPUT FILE                                
************************************************************************        
000460                                                                          
000470 01  LINE1.                                                               
000480     05  FILLER        PIC X(48) VALUE IS                                 
000490-       '****************** DEBUT DES CARTES PARAMETRES '.                
000500     05  FILLER       PIC X(32) VALUE IS ALL '*'.                         
000510     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000520 01  LINE2.                                                               
000530     05  FILLER        PIC X(40) VALUE IS                                 
000540-       '1...5...10....5...20....5...30....5...40'.                       
000550     05  FILLER        PIC X(40) VALUE IS                                 
000560-       '....5...50....5...60....5...70....5...80'.                       
000570     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000580 01  LINE3.                                                               
000590     05  FILLER        PIC X(46) VALUE IS                                 
000600-       '****************** FIN DES CARTES PARAMETRES '.                  
000610     05  FILLER       PIC X(34) VALUE IS ALL '*'.                         
000620     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000630 01  PARAMETER-LINE.                                                      
000640     05  PARAMETERS    PIC X(80).                                         
000650     05  FILLER       PIC X(53) VALUE IS SPACES.                          
000660 77  F-KEY1     PIC X(2).                                                 
000670 77  F-KEY2     PIC X(2).                                                 
000680 LINKAGE SECTION.                                                         
000690  01  LK-CARTE  PIC X(80).                                                
000700 PROCEDURE DIVISION USING LK-CARTE.                                       
000710 MAIN-PARA.                                                               
************************************************************************        
000730*         CHECKS IF THE FILE IS OPEN                                      
************************************************************************        
000750      IF WS-OPEN-FLAG NOT = 'Y'                                           
000760          PERFORM INITIALIZE-FILES                                        
000770      END-IF.                                                             
000790      PERFORM PROCESS-FILES UNTIL WS-OPEN-FLAG = 'N'.                     
000800      STOP RUN.                                                           
000810 INITIALIZE-FILES.                                                        
000820      OPEN INPUT CARD.                                                    
000830      MOVE 'Y' TO WS-OPEN-FLAG.                                           
000840      OPEN OUTPUT COUT.                                                   
000850      WRITE OUT-REC FROM LINE1                                            
000860      WRITE OUT-REC FROM LINE2.                                           
000870 PROCESS-FILES.                                                           
000880      READ CARD INTO PARAMETERS AT END SET WS-OPEN-FLAG TO 'N'.           
000890      MOVE PARAMETERS TO LK-CARTE.                                        
000900      WRITE OUT-REC FROM PARAMETER-LINE.                                  
000910      IF WS-OPEN-FLAG = 'N'                                               
000920          PERFORM TERMINATE-FILES                                         
000930      END-IF.                                                             
000940 TERMINATE-FILES.                                                         
000950      MOVE '/*' TO LK-CARTE                                               
000960      WRITE OUT-REC FROM LINE3.                                           
000970      CLOSE CARD.                                                         
000980      CLOSE COUT.
""",
        specific_demands="change close cout for go back",
        copybooks={},
        atlas_answer="",
        atlas_message_type=""
    )


def test_new_gen_with_human_feedback(state_new_gen_with_human_feedback):
    updated_state = new_generation(state_new_gen_with_human_feedback)

    # Verify that the new code is as expected
    assert "new_code" in updated_state
    assert "previous_last_gen_code" in updated_state
    # comparison_output = print_code_comparator(state_new_gen_with_human_feedback["old_code"],
    #                                           sanitize_output(updated_state["new_code"]))

    # Print comparison output for inspection
    # print(comparison_output)


@pytest.fixture
def state_extender() -> GraphState:
    return GraphState(
        files_to_process=["path/to/test_extender.cob"],
        file_metadata={"path/to/test_extender.cob": {"dependencies": []}},
        metadata={"dependencies": []},
        filename="test_extender.cob",
        critic={},
        old_code="IDENTIFICATION DIVISION.",
        previous_last_gen_code="",
        new_code="Initial code generated.",
        specific_demands="",
        copybooks={"some": "copybook data"},
        atlas_answer="",
        atlas_message_type=""
    )


def test_extender(state_extender):
    # Specify the test prompt directly for testing purposes
    test_prompt = "???"

    # Call the extender function, potentially making a real call to OpenAI
    updated_state = extender(state_extender, template=test_prompt)

    # Since we're making real calls, the specifics of the response might vary.
    # Here, ensure that new_code is extended properly.
    assert len(updated_state["new_code"]) > len(state_extender["new_code"])
    print(updated_state["new_code"])


@pytest.fixture
def state_determine_message_type(tmp_path) -> GraphState:
    class CodeReviewResult(BaseModel):
        description: str = Field(description="A detailed description of the code review.")
        grade: str = Field(description="The grade of the code review, e.g., 'good' or 'bad'.")

    d = tmp_path / "new_gen"
    d.mkdir()
    p = d / "new_test.cob"
    p.write_text("""
000010 IDENTIFICATION DIVISION.
000020 PROGRAM-ID. ABORT.
000030 AUTHOR.     TCS.
000040 DATE-COMPLIED.24/05/06.
************************************************************************
000060*     ISSUES AN ABEND AND STOPS THE RUN BY CALLING "CANCEL"
************************************************************************
000080 ENVIRONMENT DIVISION.
TOFANN CONFIGURATION SECTION.
TOFANN SOURCE-COMPUTER. IBM-390.
TOFANN OBJECT-COMPUTER.
TOFANN     PROGRAM COLLATING SEQUENCE EBC.
TOFANN SPECIAL-NAMES.
TOFANN     ALPHABET EBC IS EBCDIC.
************************************************************************
000160*     CONVERTED FROM ASSEMBLER ROUTINE ABORT
************************************************************************
000180 DATA DIVISION.
000190 WORKING-STORAGE SECTION.
000200 PROCEDURE DIVISION.
000210     CALL 'CANCEL'
000220     GOBACK.
""")
    return GraphState(
        files_to_process=[str(p)],
        file_metadata={str(p): {"dependencies": []}},
        metadata={"dependencies": []},
        filename="new_test.cob",
        critic={
            "description": "Upon reviewing the original, previous last generated, and newly generated COBOL code, the following observations and recommendations are made:\n\n1. **Consistency in Program Termination:** The newly generated code has reverted to using the `GOBACK` statement for program termination, aligning with the original code's approach and adhering to the previous critic's recommendation to keep the `GOBACK` statement. This ensures consistency in program termination and maintains the original functionality, which is a positive change.\n\n2. **Comment Clarity:** The newly generated code has improved comment clarity by explicitly stating the purpose of the `CALL 'CANCEL'` and `GOBACK` statements. This enhances code readability and understanding, especially for developers unfamiliar with the codebase.\n\n3. **Configuration Section Clean-Up:** Both the previous last generated and the newly generated code have cleaned up the configuration section by removing the `TOFANN` prefixes and correcting the syntax. This makes the code more standard and easier to understand.\n\nOverall, the newly generated code addresses the previous critic's concerns effectively and introduces improvements in comment clarity and configuration section formatting. No new relevant issues or discrepancies were introduced, and the changes made are beneficial for code maintainability and readability.",
            "grade": "good"
        },
        old_code=p.read_text(),
        previous_last_gen_code="",
        new_code="""
************************************************************************
000060*     ISSUES AN ABEND AND STOPS THE RUN BY CALLING "CANCEL"
************************************************************************
000080 ENVIRONMENT DIVISION.
000090 CONFIGURATION SECTION.
000100 SOURCE-COMPUTER. IBM-390.
000110 OBJECT-COMPUTER. IBM-390.
000120     PROGRAM COLLATING SEQUENCE IS EBC.
000130 SPECIAL-NAMES.
000140     ALPHABET EBC IS EBCDIC.
************************************************************************
000160*     CONVERTED FROM ASSEMBLER ROUTINE ABORT
************************************************************************
000180 DATA DIVISION.
000190 WORKING-STORAGE SECTION.
000200 PROCEDURE DIVISION.
000210     CALL 'CANCEL'    *> Terminates the program
000220     GOBACK.          *> Ensures proper program termination, maintaining original functionality
""",
        specific_demands="",
        copybooks={},
        atlas_answer="""
Error(040): 'IDENTIFICATION DIVISION' missing 'PROGRAM-ID' at line 000010.
Error(041): 'PROGRAM-ID' declaration 'ABORT' conflicts with system reserved names at line 000020.
Error(042): 'AUTHOR' statement is not followed by a period at line 000030.
Error(043): Incorrect keyword 'DATE-COMPLIED.' Perhaps you meant 'DATE-COMPILED' at line 000040.
Error(044): The 'CONFIGURATION SECTION' is misspelled or not properly introduced at line 000090.
Error(045): 'SOURCE-COMPUTER' and 'OBJECT-COMPUTER' declaration must be within the 'CONFIGURATION SECTION' at lines 000100 and 000110.
Error(046): 'PROGRAM COLLATING SEQUENCE' clause is incorrect or incomplete at line 000120.
Error(047): 'SPECIAL-NAMES' section is not properly defined at line 000130.
Error(048): Syntax error: 'ALPHABET EBC IS EBCDIC' may be out of context at line 000140.
Warning(020): Procedure 'CALL "CANCEL"' may cause runtime exception if not properly handled at line 000210.
""",
        atlas_message_type=""
    )


def test_determine_message_type(state_determine_message_type):
    updated_state = message_type_decider(state_determine_message_type)
    # see Langsmith

